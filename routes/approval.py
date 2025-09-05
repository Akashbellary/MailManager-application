from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import logging
from datetime import datetime
from utils.database import (find_responses, count_emails, find_response_by_id, 
                           update_response, find_email_by_id)
from utils.helpers import create_pagination_info

logger = logging.getLogger(__name__)

approval_bp = Blueprint('approval', __name__)

@approval_bp.route('/')
def approval_queue():
    """Show approval queue with all responses"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        status_filter = request.args.get('status', 'all')
        
        # Build filter
        mongo_filter = {}
        if status_filter != 'all':
            mongo_filter['status'] = status_filter
        
        # Get total count
        from utils.database import get_responses_collection
        total = get_responses_collection().count_documents(mongo_filter)
        
        # Get paginated responses
        skip = (page - 1) * per_page
        responses = find_responses(mongo_filter, skip=skip, limit=per_page)
        
        # Enrich responses with email data
        enriched_responses = []
        for response in responses:
            email = find_email_by_id(response['email_id'])
            response['email'] = email
            enriched_responses.append(response)
        
        # Create pagination info
        pagination = create_pagination_info(page, per_page, total)
        
        # Get status counts for tabs
        status_counts = {}
        all_statuses = ['pending', 'approved', 'sent', 'rejected']
        for status in all_statuses:
            status_counts[status] = get_responses_collection().count_documents({'status': status})
        status_counts['all'] = total
        
        return render_template('approval/approval_queue.html',
                               responses=enriched_responses,
                               pagination=pagination,
                               status_filter=status_filter,
                               status_counts=status_counts)
    
    except Exception as e:
        logger.error(f"Error loading approval queue: {e}")
        flash('Error loading approval queue.', 'danger')
        return render_template('approval/approval_queue.html',
                               responses=[],
                               pagination={'page': 1, 'total': 0, 'total_pages': 0},
                               status_filter='all',
                               status_counts={})

@approval_bp.route('/<response_id>')
def approval_detail(response_id):
    """Show response details for approval"""
    try:
        response = find_response_by_id(response_id)
        if not response:
            flash('Response not found.', 'danger')
            return redirect(url_for('approval.approval_queue'))
        
        # Get related email
        email = find_email_by_id(response['email_id'])
        
        return render_template('approval/approval_detail.html',
                               response=response,
                               email=email)
    
    except Exception as e:
        logger.error(f"Error loading approval detail: {e}")
        flash('Error loading response details.', 'danger')
        return redirect(url_for('approval.approval_queue'))

@approval_bp.route('/<response_id>/approve', methods=['POST'])
def approve_response(response_id):
    """Approve a response"""
    try:
        response = find_response_by_id(response_id)
        if not response:
            flash('Response not found.', 'danger')
            return redirect(url_for('approval.approval_queue'))
        
        if response['status'] != 'pending':
            flash('Response is not pending approval.', 'warning')
            return redirect(url_for('approval.approval_detail', response_id=response_id))
        
        # Update response status
        update_data = {
            'status': 'approved',
            'approved_by': 'admin',  # In real app, use current user
            'updated_at': datetime.utcnow().isoformat()
        }
        
        success = update_response(response_id, update_data)
        
        if success:
            flash('Response approved successfully!', 'success')
        else:
            flash('Failed to approve response.', 'danger')
        
        return redirect(url_for('approval.approval_detail', response_id=response_id))
    
    except Exception as e:
        logger.error(f"Error approving response: {e}")
        flash('Error approving response.', 'danger')
        return redirect(url_for('approval.approval_queue'))

@approval_bp.route('/<response_id>/reject', methods=['POST'])
def reject_response(response_id):
    """Reject a response"""
    try:
        response = find_response_by_id(response_id)
        if not response:
            flash('Response not found.', 'danger')
            return redirect(url_for('approval.approval_queue'))
        
        if response['status'] != 'pending':
            flash('Response is not pending approval.', 'warning')
            return redirect(url_for('approval.approval_detail', response_id=response_id))
        
        # Update response status
        update_data = {
            'status': 'rejected',
            'updated_at': datetime.utcnow().isoformat()
        }
        
        success = update_response(response_id, update_data)
        
        if success:
            flash('Response rejected.', 'info')
        else:
            flash('Failed to reject response.', 'danger')
        
        return redirect(url_for('approval.approval_detail', response_id=response_id))
    
    except Exception as e:
        logger.error(f"Error rejecting response: {e}")
        flash('Error rejecting response.', 'danger')
        return redirect(url_for('approval.approval_queue'))

@approval_bp.route('/<response_id>/send', methods=['POST'])
def send_response(response_id):
    """Mark response as sent"""
    try:
        response = find_response_by_id(response_id)
        if not response:
            flash('Response not found.', 'danger')
            return redirect(url_for('approval.approval_queue'))
        
        if response['status'] != 'approved':
            flash('Response must be approved before sending.', 'warning')
            return redirect(url_for('approval.approval_detail', response_id=response_id))
        
        # Update response status
        update_data = {
            'status': 'sent',
            'sent_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        success = update_response(response_id, update_data)
        
        if success:
            flash('Response marked as sent!', 'success')
        else:
            flash('Failed to mark response as sent.', 'danger')
        
        return redirect(url_for('approval.approval_detail', response_id=response_id))
    
    except Exception as e:
        logger.error(f"Error sending response: {e}")
        flash('Error marking response as sent.', 'danger')
        return redirect(url_for('approval.approval_queue'))

@approval_bp.route('/<response_id>/edit', methods=['POST'])
def edit_response(response_id):
    """Edit response text"""
    try:
        response = find_response_by_id(response_id)
        if not response:
            flash('Response not found.', 'danger')
            return redirect(url_for('approval.approval_queue'))
        
        new_text = request.form.get('response_text', '').strip()
        if not new_text:
            flash('Response text cannot be empty.', 'danger')
            return redirect(url_for('approval.approval_detail', response_id=response_id))
        
        # Update response text and reset status to pending if it was approved
        update_data = {
            'response_text': new_text,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if response['status'] == 'approved':
            update_data['status'] = 'pending'
        
        success = update_response(response_id, update_data)
        
        if success:
            flash('Response updated successfully!', 'success')
        else:
            flash('Failed to update response.', 'danger')
        
        return redirect(url_for('approval.approval_detail', response_id=response_id))
    
    except Exception as e:
        logger.error(f"Error editing response: {e}")
        flash('Error updating response.', 'danger')
        return redirect(url_for('approval.approval_queue'))

@approval_bp.route('/api/stats')
def api_approval_stats():
    """API endpoint for approval statistics"""
    try:
        from utils.database import get_responses_collection
        
        # Get status counts
        status_counts = {}
        all_statuses = ['pending', 'approved', 'sent', 'rejected']
        for status in all_statuses:
            status_counts[status] = get_responses_collection().count_documents({'status': status})
        
        return jsonify({
            'success': True,
            'status_counts': status_counts
        })
    
    except Exception as e:
        logger.error(f"Error getting approval stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
