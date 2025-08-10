from faker import Faker
from app.db.mongodb import get_db
import random

fake = Faker()

def generate_events(num=100):
    db = get_db()
    articles = list(db.articles.find({}, {"_id": 1}))
    
    for _ in range(num):
        db.events.insert_one({
            "article_id": random.choice(articles)["_id"],
            "user_location": {
                "type": "Point",
                "coordinates": [fake.longitude(), fake.latitude()]
            },
            "event_type": random.choice(["view", "click", "share"]),
            "timestamp": fake.date_time_this_year()
        })