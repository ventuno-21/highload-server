import time
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from pymongo import MongoClient
from celery import shared_task

from project.celery import prometheus_task
from project.mongo import mongo_db

# mongo_client = MongoClient(
#     settings.MONGO_URI,
#     maxPoolSize=50,  # number of asynchrounous connection
#     minPoolSize=5,
#     serverSelectionTimeoutMS=5000,
# )

# db = mongo_client[settings.MONGO_DB]


@shared_task(bind=True)
@prometheus_task
def long_task(self, payload):
    # simulate heavy cpu/io task
    time.sleep(5)
    # write an event to mongo

    mongo_db.request_events.insert_one(
        {"type": "long_task_done", "payload": payload, "ts": timezone.now()}
    )
    return {
        "status": "done",
        "result": "$$$$ $$$$ $$$$ your task sleep fpr 5 seconds and then this message shown up.$$$$ $$$$ $$$$ ",
    }
