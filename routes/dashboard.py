from flask import Blueprint, render_template, request, jsonify
import logging
from utils.database import find_emails, count_emails, find_responses
from utils.helpers import calculate_stats, safe_json_encode

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    """Dashboard with statistics and recent emails"""
    try:
        # Get recent emails
        recent_emails = find_emails({}, skip=0, limit=10)
        
        # Get all emails for statistics
        all_emails = find_emails({}, skip=0, limit=1000)  # Limit for performance
        
        # Calculate statistics
        stats = calculate_stats(all_emails)
        
        # Get response statistics
        all_responses = find_responses({}, skip=0, limit=1000)
        response_stats = {
            'pending': len([r for r in all_responses if r.get('status') == 'pending']),
            'approved': len([r for r in all_responses if r.get('status') == 'approved']),
            'sent': len([r for r in all_responses if r.get('status') == 'sent']),
            'rejected': len([r for r in all_responses if r.get('status') == 'rejected'])
        }
        
        # Prepare chart data
        chart_data = {
            'priority': {
                'labels': ['High', 'Medium', 'Low'],
                'data': [
                    stats['priority_stats']['High Priority'],
                    stats['priority_stats']['Medium Priority'],
                    stats['priority_stats']['Low Priority']
                ]
            },
            'sentiment': {
                'labels': ['Positive', 'Neutral', 'Negative'],
                'data': [
                    stats['sentiment_stats']['Positive'],
                    stats['sentiment_stats']['Neutral'],
                    stats['sentiment_stats']['Negative']
                ]
            },
            'responses': {
                'labels': ['Pending', 'Approved', 'Sent', 'Rejected'],
                'data': [
                    response_stats['pending'],
                    response_stats['approved'],
                    response_stats['sent'],
                    response_stats['rejected']
                ]
            }
        }
        
        return render_template('dashboard.html',
                               recent_emails=recent_emails,
                               total_emails=stats['total_emails'],
                               filtered_count=stats['filtered_count'],
                               response_stats=response_stats,
                               chart_data=safe_json_encode(chart_data))
    
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('dashboard.html',
                               recent_emails=[],
                               total_emails=0,
                               filtered_count=0,
                               response_stats={},
                               chart_data=safe_json_encode({}))

@dashboard_bp.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        # Get all emails for statistics
        all_emails = find_emails({}, skip=0, limit=1000)
        stats = calculate_stats(all_emails)
        
        # Get response statistics
        all_responses = find_responses({}, skip=0, limit=1000)
        response_stats = {
            'pending': len([r for r in all_responses if r.get('status') == 'pending']),
            'approved': len([r for r in all_responses if r.get('status') == 'approved']),
            'sent': len([r for r in all_responses if r.get('status') == 'sent']),
            'rejected': len([r for r in all_responses if r.get('status') == 'rejected'])
        }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'response_stats': response_stats
        })
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
