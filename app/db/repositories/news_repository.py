from app.services.llm_service import GeminiService  # Changed from GeminiService to GeminiService
from app.db.mongodb import get_db
from typing import List, Dict
import json

llm = GeminiService()  # Initialize GeminiService instead of GeminiService

def generate_and_store_articles(count: int = 5) -> None:
    """
    Generates sample news articles using Gemini and stores them in MongoDB.
    Only generates if the collection is empty.
    """
    db = get_db()
    
    if db.articles.count_documents({}) == 0:  # Only generate if DB is empty
        articles, error = llm.generate_news_articles(count)
        
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
    generate_and_store_articles()  # Ensure data exists
    return list(get_db().articles.find(
        {"category": category},
        {"_id": 0}  # Exclude MongoDB's default ID field
    ).limit(limit))