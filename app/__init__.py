# app/__init__.py
from flask import Flask
from .config.settings import Config

def create_app(test_config=None):
    """Application factory function"""
    app = Flask(__name__)
    
    # Configure application
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    from .db.mongodb import init_db
    init_db(app)

    # Register blueprints
    from .controllers.news_controller import news_bp
    # from .controllers.trending_controller import trending_bp
    
    app.register_blueprint(news_bp)
    # app.register_blueprint(trending_bp)

    return app

# Optional: Control what's exported with 'from app import *'
__all__ = ['create_app']