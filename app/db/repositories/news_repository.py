from app.services.llm_service import GeminiService  # Changed from GeminiService to GeminiService
from app.db.mongodb import get_db
from typing import List, Dict
import json

llm = GeminiService()  # Initialize GeminiService instead of GeminiService

def generate_and_store_articles(category: str, count: int = 5) -> None:
    """
    Generates sample news articles using Gemini and stores them in MongoDB.
    Only generates if the collection is empty.
    """
    db = get_db()
    
    if db.articles.count_documents({"category": category}) < 10:  # Only generate if DB is empty
        articles, error = llm.generate_news_articles(category,count)
        
        if error:
            print(f"LLM Error: {error}")
            articles = llm._get_fallback_articles(count)  # Use fallback data if API fails
        
        # Generate summaries for each article
        for article in articles:
            summary, summary_error = llm.generate_summary(
                f"{article['title']}. {article['description']}"
            )
            if summary_error:
                print(f"Summary Error: {summary_error}")
                # Fallback: Use the first 200 chars of description if summary fails
                summary = article['description'][:200] + "..."
            article['llm_summary'] = summary
        
        try:
            db.articles.insert_many(articles)
            print(f"Successfully inserted {len(articles)} articles.")
        except Exception as e:
            print(f"Database Error: Failed to insert articles. {str(e)}")

def get_articles_by_category(category: str, limit: int = 5) -> List[Dict]:
    """
    Retrieves articles by category from MongoDB.
    Automatically generates sample data if the collection is empty.
    """
    generate_and_store_articles(category, limit)  # Ensure data exists
    return list(get_db().articles.find(
        {"category": category},
        {"_id": 0}  # Exclude MongoDB's default ID field
    ).limit(limit))


def get_articles_by_score(min_score: float = 0.7, limit: int = 5) -> List[Dict]:
    db = get_db()
    articles = list(db.articles.find(
        {"relevance_score": {"$gte": min_score}},
        {"_id": 0}
    ).limit(limit))
    
    if len(articles) < limit:
        # Generate and store more articles if insufficient in DB
        generate_and_store_articles('', limit - len(articles))
        # Re-query DB after generation
        articles = list(db.articles.find(
            {"relevance_score": {"$gte": min_score}},
            {"_id": 0}
        ).limit(limit))
    
    return articles


def search_articles(query: str, limit: int = 5) -> List[Dict]:
    db = get_db()
    db.articles.create_index([("title", "text"), ("description", "text")])
    
    articles = list(db.articles.find(
        {"$text": {"$search": query}},
        {"_id": 0, "score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit))
    
    if len(articles) < limit:
        generate_and_store_articles('', limit - len(articles))
        articles = list(db.articles.find(
            {"$text": {"$search": query}},
            {"_id": 0, "score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit))
        
    return articles


def get_articles_by_source(source: str, limit: int = 5) -> List[Dict]:
    db = get_db()
    articles = list(db.articles.find(
        {"source_name": {"$regex": f"^{source}$", "$options": "i"}},
        {"_id": 0}
    ).limit(limit))
    
    if len(articles) < limit:
        generate_and_store_articles('', limit - len(articles))
        articles = list(db.articles.find(
            {"source_name": {"$regex": f"^{source}$", "$options": "i"}},
            {"_id": 0}
        ).limit(limit))
    
    return articles


def get_articles_nearby(lat: float, lon: float, radius_km: float = 10, limit: int = 5) -> List[Dict]:
    db = get_db()
    radius_meters = radius_km * 1000
    db.articles.create_index([("location", "2dsphere")])
    
    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lon, lat]},
                "distanceField": "distance_meters",
                "maxDistance": radius_meters,
                "spherical": True,
                "limit": limit
            }
        }
    ]
    
    results = list(db.articles.aggregate(pipeline))
    
    if len(results) < limit:
        generate_and_store_articles('', limit - len(results))
        results = list(db.articles.aggregate(pipeline))
    
    for article in results:
        article["_id"] = str(article["_id"])
        article["distance_km"] = round(article.pop("distance_meters", 0) / 1000, 2)
    
    return results
