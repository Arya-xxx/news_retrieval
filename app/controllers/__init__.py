# app/controllers/__init__.py
# Expose all blueprints for easy importing
from .news_controller import news_bp
from .user_controller  import auth_bp
# from .trending_controller import trending_bp

__all__ = ['news_bp', 'auth_bp']