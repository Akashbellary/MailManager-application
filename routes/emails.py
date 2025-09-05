import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, stream_template
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
from utils.database import (find_emails, count_emails, find_email_by_id, 
                           insert_response, find_responses_by_email_id, find_progress_by_id)
from utils.helpers import parse_filter_params, build_mongo_filter, create_pagination_info, sanitize_filename
from services.email_processor import email_processor
from services.ai_service import ai_service
from models import Response
import json

logger = logging.getLogger(__name__)

emails_bp = Blueprint('emails', __name__)

@emails_bp.route('/')
def email_list():
    """List emails with filtering and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        search_query = request.args.get('q', '').strip()
        
        # Parse filters
        filters = parse_filter_params(request.args)
        
        # Build MongoDB filter
        mongo_filter = build_mongo_filter(filters, search_query)
        
        # Get total count
        total = count_emails(mongo_filter)
        
        # Get paginated emails
        skip = (page - 1) * per_page
        emails = find_emails(mongo_filter, skip=skip, limit=per_page)
        
        # Create pagination info
        pagination = create_pagination_info(page, per_page, total)
        
        return render_template('emails/email_list.html',
                               emails=emails,
                               pagination=pagination,
                               search_query=search_query,
                               priority_filter=filters.get('priority', []),
                               sentiment_filter=filters.get('sentiment', []),
                               classification_filter=filters.get('classification', []),
                               search_results=bool(search_query))
    
    except Exception as e:
        logger.error(f"Error loading email list: {e}")
        flash('Error loading emails. Please try again.', 'danger')
        return render_template('emails/email_list.html',
                               emails=[],
                               pagination={'page': 1, 'total': 0, 'total_pages': 0},
                               search_query='',
                               priority_filter=[],
                               sentiment_filter=[],
                               classification_filter=[])

@emails_bp.route('/<email_id>')
def email_detail(email_id):
    """Show email details"""
    try:
        email = find_email_by_id(email_id)
        if not email:
            flash('Email not found.', 'danger')
            return redirect(url_for('emails.email_list'))
        
        # Get related draft responses
        email_drafts = find_responses_by_email_id(email_id)
        
        return render_template('emails/email_detail.html',
                               email=email,
                               email_drafts=email_drafts)
    
    except Exception as e:
        logger.error(f"Error loading email detail: {e}")
        flash('Error loading email details.', 'danger')
        return redirect(url_for('emails.email_list'))

@emails_bp.route('/upload')
def upload_form():
    """Show CSV upload form"""
    return render_template('emails/upload.html')

@emails_bp.route('/upload', methods=['POST'])
def upload_csv():
    """Handle CSV file upload"""
    try:
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(url_for('emails.upload_form'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('emails.upload_form'))
        
        if not file.filename or not file.filename.lower().endswith('.csv'):
            flash('Please select a CSV file.', 'danger')
            return redirect(url_for('emails.upload_form'))
        
        # Secure filename
        filename = secure_filename(file.filename or 'upload.csv')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Save file
        upload_folder = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Start processing
        progress_id = email_processor.process_csv_file(file_path, filename)
        
        # Redirect to progress page
        return redirect(url_for('emails.upload_progress', progress_id=progress_id))
    
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        flash(f'Error uploading file: {str(e)}', 'danger')
        return redirect(url_for('emails.upload_form'))

@emails_bp.route('/upload/progress/<progress_id>')
def upload_progress(progress_id):
    """Show upload progress page"""
    try:
        progress = find_progress_by_id(progress_id)
        if not progress:
            flash('Upload progress not found.', 'danger')
            return redirect(url_for('emails.upload_form'))
        
        return render_template('emails/upload_progress.html', progress=progress)
    
    except Exception as e:
        logger.error(f"Error loading progress: {e}")
        flash('Error loading upload progress.', 'danger')
        return redirect(url_for('emails.upload_form'))

@emails_bp.route('/upload/progress/<progress_id>/stream')
def upload_progress_stream(progress_id):
    """Server-Sent Events stream for upload progress"""
    def generate():
        try:
            while True:
                progress = find_progress_by_id(progress_id)
                if not progress:
                    yield f"data: {json.dumps({'error': 'Progress not found'})}\n\n"
                    break
                
                data = {
                    'status': progress['status'],
                    'processed_rows': progress['processed_rows'],
                    'total_rows': progress['total_rows'],
                    'percentage': progress.get('progress_percentage', 0) if hasattr(progress, 'progress_percentage') else (
                        (progress['processed_rows'] / progress['total_rows'] * 100) if progress['total_rows'] > 0 else 0
                    ),
                    'error_message': progress.get('error_message', '')
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                
                if progress['status'] in ['completed', 'failed']:
                    break
                
                # Wait 1 second before next update
                import time
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in progress stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@emails_bp.route('/<email_id>/generate-response', methods=['POST'])
def generate_response(email_id):
    """Generate AI response for email"""
    try:
        email = find_email_by_id(email_id)
        if not email:
            flash('Email not found.', 'danger')
            return redirect(url_for('emails.email_list'))
        
        # Check if we should use suggested response
        use_suggested = request.form.get('use_suggested') == 'true'
        
        if use_suggested and email.get('suggested_responses'):
            response_text = email['suggested_responses'][0]
        else:
            # Generate new response
            response_text = ai_service.generate_response(
                email['email_subject'],
                email['email_body'],
                email['classification']
            )
        
        if not response_text:
            flash('Failed to generate response. Please try again.', 'danger')
            return redirect(url_for('emails.email_detail', email_id=email_id))
        
        # Create response document
        response_data = Response({
            'email_id': email_id,
            'response_text': response_text,
            'status': 'pending',
            'recipient': email['sender'],
            'subject': f"Re: {email['email_subject']}"
        }).to_dict()
        
        # Save response
        response_id = insert_response(response_data)
        
        flash('Response generated successfully!', 'success')
        return redirect(url_for('approval.approval_detail', response_id=response_id))
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        flash('Error generating response. Please try again.', 'danger')
        return redirect(url_for('emails.email_detail', email_id=email_id))
