import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv('MONGO_URI')
    DB_NAME = os.getenv('DB_NAME')
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')