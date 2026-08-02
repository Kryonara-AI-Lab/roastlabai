import os
import secrets
from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    # Load SECRET_KEY from environment variables for session protection
    # Fall back to a cryptographically secure random 32-byte hex string to prevent session tampering/hijacking
    secret_key = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app