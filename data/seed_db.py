import json
from app.db.mongodb import get_db

def seed_data():
    db = get_db()
    with open("data/news_data.json") as f:
        articles = json.load(f)
    
    db.articles.delete_many({})
    db.articles.insert_many(articles)
    print(f"Inserted {db.articles.count_documents({})} articles")

if __name__ == "__main__":
    seed_data()