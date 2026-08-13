from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    # SECURITY REFLECTION: Avoid hardcoding cryptographic session keys.
    # Load from environment variable with high-entropy fallback.
    import os
    import secrets
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret_key,
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app