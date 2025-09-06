from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
from services.auth.gmail_service import gmail_service

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/google-login')
def google_login():
    """Initiate Google OAuth flow"""
    try:
        authorization_url = gmail_service.authenticate_user()
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error initiating Google login: {e}")
        flash('Error initiating Google login. Please try again.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

@auth_bp.route('/google-callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Get the full URL including query parameters
        authorization_response = request.url
        
        # Handle OAuth callback
        result = gmail_service.handle_callback(authorization_response)
        
        if result['success']:
            # Store user info in session
            session['user_email'] = result['user_info'].get('email')
            session['user_name'] = result['user_info'].get('name')
            flash(f'Successfully logged in as {session["user_name"]}', 'success')
            
            # Redirect to sync emails
            return redirect(url_for('auth.sync_emails'))
        else:
            flash(f'Authentication failed: {result.get("error", "Unknown error")}', 'danger')
            return redirect(url_for('dashboard.dashboard'))
            
    except Exception as e:
        logger.error(f"Error handling Google callback: {e}")
        flash('Error during authentication. Please try again.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

@auth_bp.route('/sync-emails')
def sync_emails():
    """Sync emails from Gmail to database"""
    try:
        if 'user_email' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.google_login'))
        
        # Sync emails
        result = gmail_service.sync_emails_to_db(session['user_email'])
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(f'Error syncing emails: {result.get("error", "Unknown error")}', 'danger')
            
        return redirect(url_for('emails.email_list'))
        
    except Exception as e:
        logger.error(f"Error syncing emails: {e}")
        flash('Error syncing emails. Please try again.', 'danger')
        return redirect(url_for('emails.email_list'))

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    try:
        # Clear session
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('dashboard.dashboard'))
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        flash('Error during logout.', 'danger')
        return redirect(url_for('dashboard.dashboard'))