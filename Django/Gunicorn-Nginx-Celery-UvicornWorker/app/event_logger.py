from datetime import datetime

from django.conf import settings
from django.utils import timezone
from pymongo import MongoClient

client = MongoClient(settings.MONGO_URI, maxPoolSize=20)
db = client[settings.MONGO_DB]


def log_event(event_type: str, endpoint: str, method: str, payload=None):
    """Insert a new event into MongoDB."""
    doc = {
        "type": event_type,
        "endpoint": endpoint,
        "method": method,
        "payload": payload or {},
        "ts": timezone.now(),
    }
    db.events.insert_one(doc)
