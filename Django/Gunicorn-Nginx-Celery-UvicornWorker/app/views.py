import asyncio
import json
import time
import uuid

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator, sync_and_async_middleware
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from drf_spectacular.utils import extend_schema
from prometheus_client import Histogram
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from project.mongo import mongo_db

from .metrics import API_LATENCY, API_REQUEST_COUNT, CACHE_HIT, CACHE_MISS
from .models import Item, RequestLog
from .serializers import ItemSerializer, MongoEventSerializer
from .tasks import long_task

BACKPRESSURE_ENABLED = getattr(settings, "BACKPRESSURE_ENABLED", False)
BACKPRESSURE_SLEEP_20MS = getattr(settings, "BACKPRESSURE_SLEEP_20MS", 0.02)  # 20ms


def apply_sync_backpressure():
    if BACKPRESSURE_ENABLED:
        time.sleep(BACKPRESSURE_SLEEP_20MS)


async def apply_async_backpressure():
    if BACKPRESSURE_ENABLED:
        await asyncio.sleep(BACKPRESSURE_SLEEP_20MS)


# --------------------
# DRF views
# --------------------
class DRFSyncGetAPI(APIView):
    # Per-View Cache: 15 seconds the result will be the same
    @method_decorator(cache_page(15))
    def get(self, request):
        API_REQUEST_COUNT.labels(endpoint="drf_sync_get", method="GET").inc()
        with API_LATENCY.labels(endpoint="drf_sync_get", method="GET").time():
            t0 = time.time()
            count = Item.objects.count()
            mongo_db.request_events.insert_one(
                {
                    "type": "sync_get",
                    "ts": time.time(),
                }
            )

            return Response(
                {"items_count": count, "duration_ms": (time.time() - t0) * 1000}
            )


class DRFSyncPostAPI(APIView):

    @extend_schema(
        request=ItemSerializer,
        responses=ItemSerializer,
    )
    def post(self, request):
        t0 = time.time()

        serializer = ItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()

        mongo_db.request_events.insert_one(
            {"type": "sync_post", "name": item.name, "ts": time.time()}
        )

        return Response(
            {
                "item": ItemSerializer(item).data,
                "duration_ms": (time.time() - t0) * 1000,
            },
            status=status.HTTP_201_CREATED,
        )


# --------------------
# JSon endpoints
# --------------------
@require_GET
def json_sync_get_view(request):

    API_REQUEST_COUNT.labels(endpoint="json_sync_get", method="GET").inc()
    with API_LATENCY.labels(endpoint="json_sync_get", method="GET").time():
        apply_sync_backpressure()  # 🔥 Backpressure

        t0 = time.time()
        count = Item.objects.count()

        mongo_db.request_events.insert_one({"type": "sync_get", "ts": time.time()})

        duration = (time.time() - t0) * 1000
        return JsonResponse({"items_count": count, "duration_ms": duration})


class JsonSyncPostView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # @method_decorator(csrf_exempt)
    def post(self, request):
        t0 = time.time()

        # --- Check content-type ---
        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type:
            # JSON mode
            try:
                body = json.loads(request.body.decode("utf-8"))
            except Exception:
                return JsonResponse({"error": "Invalid JSON"}, status=400)

            name = body.get("name", "no-name")

        else:
            # Form mode (x-www-form-urlencoded or multipart/form-data)
            name = request.POST.get("name", "no-name")

        # --- Save item ---
        item = Item.objects.create(name=name, value=1)

        mongo_db.request_events.insert_one(
            {
                "type": "sync_post",
                "name": name,
                "ts": time.time(),
            }
        )

        duration = (time.time() - t0) * 1000

        return JsonResponse({"id": item.id, "duration_ms": duration})


async def json_async_get_view(request):
    t0 = time.time()

    cache_key = "items_count_v1"

    # Low-Level Cache (cache.get / cache.set)
    cached_count = cache.get(cache_key)
    if cached_count is None:

        # adding prometheus metric
        CACHE_MISS.labels(key=cache_key).inc()
        # cache miss
        count = await sync_to_async(Item.objects.count)()
        # If we use redis library directly belew line will be: redis_client.set("a", "b", ex=30)
        cache.set(cache_key, count, timeout=30)  # 30 seconds
    else:
        # adding prometheus metric
        CACHE_HIT.labels(key=cache_key).inc()
        # cache hit
        count = cached_count

    # instead of below line we use caching to store count
    # count = await sync_to_async(Item.objects.count)()

    await sync_to_async(mongo_db.request_events.insert_one)(
        {"type": "async_get", "ts": time.time()}
    )

    duration = (time.time() - t0) * 1000
    return JsonResponse({"items_count": count, "duration_ms": duration})


@csrf_exempt
async def json_async_post_view(request):

    await apply_async_backpressure()  # 🔥 Backpressure

    t0 = time.time()

    body = await sync_to_async(lambda: request.POST)()

    name = body.get("name", "no-name")

    item = await sync_to_async(Item.objects.create)(name=name, value=2)

    await sync_to_async(mongo_db.request_events.insert_one)(
        {"type": "async_post", "name": name, "ts": time.time()}
    )

    duration = (time.time() - t0) * 1000
    return JsonResponse({"id": item.id, "duration_ms": duration})


# Sync POST - enqueue to celery (non-blocking)
@require_POST
@csrf_exempt
def json_sync_post_with_celery(request):
    payload = json.loads(request.body or "{}")
    task = long_task.delay(payload)
    # Invalidate relevant caches if needed
    # cache.delete_pattern("some_cache_prefix*")
    return JsonResponse(
        {
            "task_id": task.id,
            "payload": payload,
            "info": "Your task is on Process with celery",
        },
        status=202,
    )


class MongoEventsView(View):
    def get(self, request):
        start = time.time()

        events_cursor = mongo_db.request_events.find().sort("_id", -1).limit(50)

        events = []
        for doc in events_cursor:
            doc["_id"] = str(doc["_id"])
            events.append(doc)

        if not events:
            return JsonResponse(
                {
                    "status": "empty",
                    "message": "No events found in request_events collection.",
                    "events": [],
                    "count": 0,
                    "duration_ms": (time.time() - start) * 1000,
                },
                status=200,
            )

        return JsonResponse(
            {
                "status": "ok",
                "count": len(events),
                "duration_ms": (time.time() - start) * 1000,
                "events": events,
            },
            status=200,
        )


# health
def health(request):
    return JsonResponse({"status": "ok"})


# --------------------
# other views not api
# --------------------


def dashboard(request):
    items = Item.objects.all()
    now = time.time()
    return render(request, "dashboard.html", {"items": items, "now": now})


# --------------------
# Not works properly
# --------------------
@require_GET
def check(request):
    from prometheus_client import REGISTRY

    registered_metrics = list(REGISTRY.collect())

    return JsonResponse(
        {
            "status": "ok",
            "registered_metrics": registered_metrics,
        }
    )


# TODO: below class will not work, search and find out why
@api_view(["POST"])
async def drf_async_post_view(request):
    start = time.time()

    serializer = ItemSerializer(data=request.data)
    await sync_to_async(serializer.is_valid)(raise_exception=True)
    item = await sync_to_async(serializer.save)()

    await sync_to_async(mongo_db.request_events.insert_one)(
        {
            "type": "async_post",
            "name": item.name,
            "ts": time.time(),
            "duration_ms": (time.time() - start) * 1000,
        }
    )

    return Response(
        {
            "item": ItemSerializer(item).data,
            "duration_ms": (time.time() - start) * 1000,
        }
    )


# TODO: below class will not work, search and find out why
class AsyncPostAPI(APIView):
    def post(self, request, *args, **kwargs):
        # return async_to_sync(self.async_post)(request)
        return asyncio.run(self.async_post)(request)

    async def async_post(self, request):
        start = time.time()

        serializer = ItemSerializer(data=request.data)
        await sync_to_async(serializer.is_valid)(raise_exception=True)
        item = await sync_to_async(serializer.save)()

        await sync_to_async(mongo_db.request_events.insert_one)(
            {"type": "async_post", "name": item.name, "ts": time.time()}
        )

        return Response(
            {
                "item": ItemSerializer(item).data,
                "duration_ms": (time.time() - start) * 1000,
            }
        )


# --------------------
# OLD views
# --------------------
# # Async GET - cache_page (per-view)
# @cache_page(30)
# async def async_get(request):
#     # simulate async DB op (if you have async ORM)
#     # here just return random id
#     return JsonResponse({"type": "async_get", "id": str(uuid.uuid4())})

# # Async POST - idempotent computational example, low-level cache
# async def async_post(request):
#     body = await request.json()
#     # create a stable key from body for idempotency
#     key = "async_post:" + str(hash(json.dumps(body, sort_keys=True)))
#     cached = cache.get(key)
#     if cached:
#         return JsonResponse({"cached": True, "result": cached})
#     # simulate heavy compute (call external async or CPU task)
#     result = {"echo": body, "id": str(uuid.uuid4())}
#     cache.set(key, result, timeout=60 * 5)
#     return JsonResponse({"cached": False, "result": result})

# # Sync GET - per-view cache (DB query)
# @cache_page(30)
# def sync_get(request):
#     count = Item.objects.count()
#     return JsonResponse({"type": "sync_get", "count": count})

# # Sync POST - enqueue to celery (non-blocking)
# def sync_post(request):
#     payload = json.loads(request.body or "{}")
#     task = long_task.delay(payload)
#     # Invalidate relevant caches if needed
#     cache.delete_pattern("some_cache_prefix*")
# return JsonResponse({"task_id": task.id}, status=202)
