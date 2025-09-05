import logging
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, timedelta
import json

from services.mongodb_service import mongodb_service
from services.approval_service import approval_service

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get email statistics
        total_emails_result = mongodb_service.get_emails(page_size=1)
        total_emails = total_emails_result.get("total", 0)
        
        # Get priority distribution
        priority_stats = {}
        for priority in ["High Priority", "Medium Priority", "Low Priority"]:
            result = mongodb_service.get_emails(
                filters={"priority": priority},
                page_size=1
            )
            priority_stats[priority] = result.get("total", 0)
        
        # Get sentiment distribution
        sentiment_stats = {}
        for sentiment in ["Positive", "Neutral", "Negative"]:
            result = mongodb_service.get_emails(
                filters={"sentiment": sentiment},
                page_size=1
            )
            sentiment_stats[sentiment] = result.get("total", 0)
        
        # Get filtered emails count
        filtered_result = mongodb_service.get_emails(
            filters={"filtered": True},
            page_size=1
        )
        filtered_count = filtered_result.get("total", 0)
        
        # Get response statistics
        response_stats = approval_service.get_response_statistics()
        
        # Get recent emails
        recent_emails_result = mongodb_service.get_emails(
            page=1,
            page_size=10,
            sort=[("metadata.date_epoch", -1)]
        )
        recent_emails = recent_emails_result.get("data", [])
        
        # Format data for charts
        chart_data = {
            "priority": {
                "labels": ["High", "Medium", "Low"],
                "data": [
                    priority_stats.get("High Priority", 0),
                    priority_stats.get("Medium Priority", 0),
                    priority_stats.get("Low Priority", 0)
                ]
            },
            "sentiment": {
                "labels": ["Positive", "Neutral", "Negative"],
                "data": [
                    sentiment_stats.get("Positive", 0),
                    sentiment_stats.get("Neutral", 0),
                    sentiment_stats.get("Negative", 0)
                ]
            },
            "responses": {
                "labels": ["Pending", "Approved", "Sent", "Rejected"],
                "data": [
                    response_stats.get("pending", 0),
                    response_stats.get("approved", 0),
                    response_stats.get("sent", 0),
                    response_stats.get("rejected", 0)
                ]
            }
        }
        
        return render_template('dashboard.html',
                             total_emails=total_emails,
                             filtered_count=filtered_count,
                             priority_stats=priority_stats,
                             sentiment_stats=sentiment_stats,
                             response_stats=response_stats,
                             recent_emails=recent_emails,
                             chart_data=json.dumps(chart_data))
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('dashboard.html',
                             total_emails=0,
                             filtered_count=0,
                             priority_stats={},
                             sentiment_stats={},
                             response_stats={},
                             recent_emails=[],
                             chart_data=json.dumps({}))

@dashboard_bp.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        # Get email statistics
        total_emails_result = mongodb_service.get_emails(page_size=1)
        total_emails = total_emails_result.get("total", 0)
        
        # Get priority distribution
        priority_stats = {}
        for priority in ["High Priority", "Medium Priority", "Low Priority"]:
            result = mongodb_service.get_emails(
                filters={"priority": priority},
                page_size=1
            )
            priority_stats[priority] = result.get("total", 0)
        
        # Get response statistics
        response_stats = approval_service.get_response_statistics()
        
        return jsonify({
            "total_emails": total_emails,
            "priority_distribution": priority_stats,
            "response_stats": response_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500
