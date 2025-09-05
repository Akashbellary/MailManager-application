import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

from services.email_processor import email_processor
from services.search_service import search_service
from services.mongodb_service import mongodb_service
from services.approval_service import approval_service

logger = logging.getLogger(__name__)

email_bp = Blueprint('emails', __name__, url_prefix='/emails')

@email_bp.route('/')
def email_list():
    """Email list page with filtering and search"""
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('q', '', type=str)
        priority_filter = request.args.getlist('priority')
        sentiment_filter = request.args.getlist('sentiment')
        classification_filter = request.args.getlist('classification')
        
        # Build filters
        filters = {}
        if priority_filter:
            if len(priority_filter) == 1:
                filters['priority'] = priority_filter[0]
            else:
                filters['priority'] = {"$in": priority_filter}
        
        if sentiment_filter:
            if len(sentiment_filter) == 1:
                filters['sentiment'] = sentiment_filter[0]
            else:
                filters['sentiment'] = {"$in": sentiment_filter}
        
        if classification_filter:
            if len(classification_filter) == 1:
                filters['classification'] = classification_filter[0]
            else:
                filters['classification'] = {"$in": classification_filter}
        
        # Handle search
        if search_query:
            search_results = search_service.execute_search(search_query, k=20, filters=filters)
            # Convert search results to email list format
            emails = [result["email_record"] for result in search_results]
            result = {
                "data": emails,
                "total": len(emails),
                "page": 1,
                "page_size": 20,
                "total_pages": 1
            }
        else:
            # Regular pagination
            result = mongodb_service.get_emails(
                page=page,
                page_size=20,
                filters=filters,
                sort=[("metadata.date_epoch", -1)]
            )
        
        return render_template('email_list.html',
                             emails=result["data"],
                             pagination=result,
                             search_query=search_query,
                             priority_filter=priority_filter,
                             sentiment_filter=sentiment_filter,
                             classification_filter=classification_filter)
        
    except Exception as e:
        logger.error(f"Error loading email list: {e}")
        flash('Error loading emails', 'error')
        return render_template('email_list.html',
                             emails=[],
                             pagination={"data": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0},
                             search_query="",
                             priority_filter=[],
                             sentiment_filter=[],
                             classification_filter=[])

@email_bp.route('/<email_id>')
def email_detail(email_id):
    """Email detail page"""
    try:
        email = mongodb_service.get_email_by_id(email_id)
        if not email:
            flash('Email not found', 'error')
            return redirect(url_for('emails.email_list'))
        
        # Get existing draft responses for this email
        existing_drafts = mongodb_service.get_draft_responses()
        email_drafts = [draft for draft in existing_drafts["data"] if draft["email_id"] == email_id]
        
        return render_template('email_detail.html',
                             email=email,
                             email_drafts=email_drafts)
        
    except Exception as e:
        logger.error(f"Error loading email detail: {e}")
        flash('Error loading email details', 'error')
        return redirect(url_for('emails.email_list'))

@email_bp.route('/upload')
def upload_form():
    """CSV upload form"""
    return render_template('upload.html')

@email_bp.route('/upload', methods=['POST'])
def upload_csv():
    """Handle CSV file upload"""
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('emails.upload_form'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('emails.upload_form'))
        
        if not file.filename.lower().endswith('.csv'):
            flash('Please upload a CSV file', 'error')
            return redirect(url_for('emails.upload_form'))
        
        # Process the CSV file
        file_content = file.read()
        results = email_processor.process_csv_upload(file_content)
        
        flash(f'Successfully processed {results["inserted"]} emails out of {results["total_rows"]} rows', 'success')
        
        if results["failed"] > 0:
            flash(f'{results["failed"]} rows failed to process', 'warning')
        
        return redirect(url_for('emails.email_list'))
        
    except Exception as e:
        logger.error(f"Error processing CSV upload: {e}")
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('emails.upload_form'))

@email_bp.route('/<email_id>/generate_response', methods=['POST'])
def generate_response(email_id):
    """Generate draft response for email"""
    try:
        use_suggested = request.form.get('use_suggested', 'false').lower() == 'true'
        
        draft_id = approval_service.generate_draft_response(email_id, use_suggested)
        
        if draft_id:
            flash('Draft response generated successfully', 'success')
        else:
            flash('Failed to generate draft response', 'error')
        
        return redirect(url_for('emails.email_detail', email_id=email_id))
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        flash('Error generating response', 'error')
        return redirect(url_for('emails.email_detail', email_id=email_id))

@email_bp.route('/search')
def search():
    """Search emails"""
    try:
        query = request.args.get('q', '', type=str)
        if not query:
            return redirect(url_for('emails.email_list'))
        
        results = search_service.execute_search(query, k=50)
        
        return render_template('email_list.html',
                             emails=[result["email_record"] for result in results],
                             pagination={"data": [], "total": len(results), "page": 1, "page_size": 50, "total_pages": 1},
                             search_query=query,
                             priority_filter=[],
                             sentiment_filter=[],
                             classification_filter=[],
                             search_results=True)
        
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        flash('Error performing search', 'error')
        return redirect(url_for('emails.email_list'))

@email_bp.route('/api/search')
def api_search():
    """API endpoint for email search"""
    try:
        query = request.args.get('q', '', type=str)
        if not query:
            return jsonify({"error": "Query parameter required"}), 400
        
        results = search_service.execute_search(query, k=25)
        
        return jsonify({
            "results": results,
            "total": len(results)
        })
        
    except Exception as e:
        logger.error(f"Error in API search: {e}")
        return jsonify({"error": "Search failed"}), 500
