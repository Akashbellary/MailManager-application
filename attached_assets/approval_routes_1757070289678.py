import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from services.approval_service import approval_service
from services.mongodb_service import mongodb_service

logger = logging.getLogger(__name__)

approval_bp = Blueprint('approval', __name__, url_prefix='/approval')

@approval_bp.route('/')
def approval_queue():
    """Approval queue page"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'pending', type=str)
        
        result = approval_service.get_pending_responses(page=page, page_size=20)
        
        return render_template('approval_queue.html',
                             responses=result["data"],
                             pagination=result,
                             status_filter=status_filter)
        
    except Exception as e:
        logger.error(f"Error loading approval queue: {e}")
        flash('Error loading approval queue', 'error')
        return render_template('approval_queue.html',
                             responses=[],
                             pagination={"data": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0},
                             status_filter='pending')

@approval_bp.route('/<response_id>/approve', methods=['POST'])
def approve_response(response_id):
    """Approve a draft response"""
    try:
        approved_by = request.form.get('approved_by', 'admin')
        
        success = approval_service.approve_response(response_id, approved_by)
        
        if success:
            flash('Response approved and sent successfully', 'success')
        else:
            flash('Failed to approve response', 'error')
        
        return redirect(url_for('approval.approval_queue'))
        
    except Exception as e:
        logger.error(f"Error approving response: {e}")
        flash('Error approving response', 'error')
        return redirect(url_for('approval.approval_queue'))

@approval_bp.route('/<response_id>/reject', methods=['POST'])
def reject_response(response_id):
    """Reject a draft response"""
    try:
        rejected_by = request.form.get('rejected_by', 'admin')
        
        success = approval_service.reject_response(response_id, rejected_by)
        
        if success:
            flash('Response rejected', 'success')
        else:
            flash('Failed to reject response', 'error')
        
        return redirect(url_for('approval.approval_queue'))
        
    except Exception as e:
        logger.error(f"Error rejecting response: {e}")
        flash('Error rejecting response', 'error')
        return redirect(url_for('approval.approval_queue'))

@approval_bp.route('/api/stats')
def api_stats():
    """API endpoint for approval statistics"""
    try:
        stats = approval_service.get_response_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting approval stats: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500

@approval_bp.route('/api/<response_id>/preview')
def api_preview_response(response_id):
    """API endpoint to preview a draft response"""
    try:
        # Get draft response details
        responses = mongodb_service.get_draft_responses()
        draft_response = None
        
        for response in responses["data"]:
            if response["_id"] == response_id:
                draft_response = response
                break
        
        if not draft_response:
            return jsonify({"error": "Response not found"}), 404
        
        # Get original email
        email = mongodb_service.get_email_by_id(draft_response["email_id"])
        
        return jsonify({
            "draft_response": draft_response,
            "original_email": email
        })
        
    except Exception as e:
        logger.error(f"Error previewing response: {e}")
        return jsonify({"error": "Failed to preview response"}), 500
