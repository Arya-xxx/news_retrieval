# app/db/__init__.py
from .mongodb import get_db, init_db
from .repositories.news_repository import get_articles_by_category

__all__ = ['get_db', 'init_db', 'get_articles_by_category']