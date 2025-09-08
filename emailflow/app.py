import os
import logging
from flask import Flask, session
from werkzeug.middleware.proxy_fix import ProxyFix

from dotenv import load_dotenv

# Suppress TensorFlow deprecation warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='tensorflow')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='pymongo')

# load .env
load_dotenv()

# Configure logging - reduce verbosity for production
logging.basicConfig(level=logging.INFO)
# Suppress verbose MongoDB and TensorFlow logs
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('tensorflow').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('h5py').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Get the directory of the current file
basedir = os.path.abspath(os.path.dirname(__file__))

# Create Flask app with explicit template and static folder paths
app = Flask(__name__,
            template_folder=os.path.join(basedir, '..', 'templates'),
            static_folder=os.path.join(basedir, '..', 'static'))

app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, '..', 'uploads')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
from emailflow.routes.dashboard import dashboard_bp
from emailflow.routes.emails import emails_bp
from emailflow.routes.approval import approval_bp
from emailflow.routes.search import search_bp
from emailflow.routes.auth import auth_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(emails_bp, url_prefix='/emails')
app.register_blueprint(approval_bp, url_prefix='/approval')
app.register_blueprint(search_bp, url_prefix='/search')
app.register_blueprint(auth_bp, url_prefix='/auth')

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


