# app/db/repositories/__init__.py
from .news_repository import (
    get_articles_by_category,
    # get_articles_by_location,
    # search_articles
)
# from .events_repository import log_user_event, get_trending_articles

__all__ = [
    'get_articles_by_category',
    # 'get_articles_by_location',
    # 'search_articles',
    # 'log_user_event',
    # 'get_trending_articles'
]