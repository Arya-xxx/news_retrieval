# app/db/repositories/__init__.py
from .news_repository import (
    get_articles_by_category,
    get_articles_by_score,
    search_articles,
    get_articles_by_source,
    get_articles_nearby,
)

__all__ = [
    'get_articles_by_category',
    'get_articles_by_score',
    'search_articles',
    'get_articles_by_source',
    'get_articles_nearby',
]
