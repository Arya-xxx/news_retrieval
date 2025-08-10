from pymongo import MongoClient
from flask import current_app

client = None
db = None

def init_db(app):
    global client, db
    client = MongoClient(app.config['MONGO_URI'])
    db = client[app.config['DB_NAME']]

def get_db():
    if db is None:
        raise RuntimeError("Database not initialized")
    return db