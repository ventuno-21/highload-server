import time
from functools import wraps

from celery import Celery
from prometheus_client import Counter, Histogram

CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_total", "Total number of Celery tasks", ["task_name", "status"]
)
CELERY_TASKS_TIME = Histogram(
    "celery_tasks_duration_seconds", "Time spent in Celery tasks", ["task_name"]
)

app = Celery("project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# wrapper for tasks
def prometheus_task(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        start = time.time()
        try:
            result = fn(*args, **kwargs)
            CELERY_TASKS_TOTAL.labels(task_name=fn.__name__, status="success").inc()
            return result
        except Exception as e:
            CELERY_TASKS_TOTAL.labels(task_name=fn.__name__, status="failure").inc()
            raise
        finally:
            CELERY_TASKS_TIME.labels(task_name=fn.__name__).observe(time.time() - start)

    return wrapper
