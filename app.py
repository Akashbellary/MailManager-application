import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
from routes.dashboard import dashboard_bp
from routes.emails import emails_bp
from routes.approval import approval_bp
from routes.search import search_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(emails_bp, url_prefix='/emails')
app.register_blueprint(approval_bp, url_prefix='/approval')
app.register_blueprint(search_bp, url_prefix='/search')

# Root route redirect
@app.route('/')
def index():
    from flask import redirect, url_for
    return redirect(url_for('dashboard.dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    from flask import render_template
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    from flask import render_template
    app.logger.error(f'Server Error: {error}')
    return render_template('base.html'), 500

@app.errorhandler(413)
def too_large(error):
    from flask import render_template, flash, redirect, url_for
    flash('File too large. Maximum size is 100MB.', 'danger')
    return redirect(url_for('emails.upload_form'))
