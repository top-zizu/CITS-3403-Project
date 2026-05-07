import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///debate_app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False