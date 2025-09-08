from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import logging
from services.search_service import search_service
from utils.helpers import parse_filter_params, create_pagination_info

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)

@search_bp.route('/')
def search_emails():
    """Enhanced search with natural language support"""
    try:
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 20
        
        if not query:
            flash('Please enter a search query.', 'warning')
            return redirect(url_for('emails.email_list'))
        
        # Parse additional filters
        filters = parse_filter_params(request.args)
        
        # Perform search
        search_results = search_service.search_emails(query, filters, page, per_page)
        
        # Create pagination info
        pagination = create_pagination_info(
            page, 
            per_page, 
            search_results['total']
        )
        
        return render_template('emails/email_list.html',
                               emails=search_results['emails'],
                               pagination=pagination,
                               search_query=query,
                               priority_filter=filters.get('priority', []),
                               sentiment_filter=filters.get('sentiment', []),
                               classification_filter=filters.get('classification', []),
                               search_results=True,
                               query_interpretation=search_results.get('query_interpretation'))
    
    except Exception as e:
        logger.error(f"Error in search: {e}")
        flash(f'Error performing search: {str(e)}', 'danger')
        return redirect(url_for('emails.email_list'))

@search_bp.route('/api/suggestions')
def api_search_suggestions():
    """API endpoint for search suggestions"""
    try:
        query = request.args.get('q', '').strip()
        
        if len(query) < 2:
            return jsonify({'suggestions': []})
        
        suggestions = search_service.get_search_suggestions(query)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@search_bp.route('/api/interpret')
def api_interpret_query():
    """API endpoint for query interpretation"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'})
        
        from services.ai_service import ai_service
        interpretation = ai_service.interpret_search_query(query)
        
        return jsonify({
            'success': True,
            'interpretation': interpretation
        })
    
    except Exception as e:
        logger.error(f"Error interpreting query: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
