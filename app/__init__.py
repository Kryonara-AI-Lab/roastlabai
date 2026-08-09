from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    import os
    import secrets

    # Dynamic fallback generation of secret keys for security
    secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app