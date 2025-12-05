from pymongo import MongoClient
import os

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB = os.environ.get("MONGO_DB", "analytics")

client = MongoClient(MONGO_URL)
mongo_db = client[MONGO_DB]
