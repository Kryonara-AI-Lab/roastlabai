import os
import secrets
from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    # Secure the session cookies dynamically with environment lookup and secure fallback
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app