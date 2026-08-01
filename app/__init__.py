import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    # SECURITY: Load the session SECRET_KEY from the environment.
    # In production, this key MUST be securely generated (e.g., using `openssl rand -hex 32` or `python -c "import secrets; print(secrets.token_hex(32))"`)
    # and set as an environment variable. A fallback is provided for ease of development.
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'roastlab_default_dev_secret_key_change_in_production'),
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app