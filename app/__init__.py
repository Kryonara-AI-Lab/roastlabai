from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    import os
    import secrets

    # Use environment secret key with a secure fallback
    secret_key = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=not os.environ.get('FLASK_DEBUG') and not os.environ.get('DEVELOPMENT')
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app