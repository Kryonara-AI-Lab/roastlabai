import os
import secrets
from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    # Securely set SECRET_KEY dynamically using environment variable or a strong random fallback
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app