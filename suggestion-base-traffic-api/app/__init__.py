from flask import Flask
from flask_cors import CORS
from config import config
import os


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    CORS(app, resources={r'/api/*': {'origins': '*'}})

    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.get('/')
    def index():
        return {
            'service': 'Suggestion Base Traffic API',
            'version': '1.0.0',
            'docs': '/api/health',
        }

    return app
