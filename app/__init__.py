import os
import secrets
from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    # Securely retrieve the SECRET_KEY from environment variables or fallback to a secure generated token.
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app
