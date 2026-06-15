from flask import Flask
from dotenv import load_dotenv

def create_app():
    # Force loading of the local .env configuration file
    load_dotenv()
    
    app = Flask(__name__)
    
    app.config.from_mapping(
        SECRET_KEY='roastlab_secret_key_change_this_immediately',
    )

    from . import routes
    app.register_blueprint(routes.bp)

    return app