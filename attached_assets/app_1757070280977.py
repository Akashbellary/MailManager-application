import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_change_me")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure file upload
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize services
from services.mongodb_service import mongodb_service
from services.nvidia_client import nvidia_client

# Connect to MongoDB
mongodb_service.connect()

# Register blueprints
from routes.dashboard_routes import dashboard_bp
from routes.email_routes import email_bp
from routes.approval_routes import approval_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(email_bp)
app.register_blueprint(approval_bp)

@app.route('/')
def index():
    from flask import redirect, url_for
    return redirect(url_for('dashboard.dashboard'))

@app.errorhandler(404)
def not_found(error):
    from flask import render_template
    return render_template('base.html', 
                         title='Page Not Found',
                         content='<div class="alert alert-warning">Page not found.</div>'), 404

@app.errorhandler(500)
def internal_error(error):
    from flask import render_template
    logger.error(f"Internal server error: {error}")
    return render_template('base.html',
                         title='Server Error', 
                         content='<div class="alert alert-danger">Internal server error.</div>'), 500
