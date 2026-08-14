import os
import secrets
from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    # SECURITY: Dynamic secret key retrieval with secure fallback.
    # Prevents hardcoded secret key disclosure, session tampering, and cookie forgery vulnerabilities.
    secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app
