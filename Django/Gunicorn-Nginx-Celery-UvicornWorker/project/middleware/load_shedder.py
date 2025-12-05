import time
import threading
from django.http import JsonResponse
from django.conf import settings

# Shared global counters
_ACTIVE_REQUESTS = 0
_LOCK = threading.Lock()  # protect concurrent access to _ACTIVE_REQUESTS


def get_max_active_requests():
    """
    Read from Django settings or fallback to a safe default.
    Example in settings.py:
        LOAD_SHED_MAX_ACTIVE_REQUESTS = 100
    """
    return getattr(settings, "LOAD_SHED_MAX_ACTIVE_REQUESTS", 50)


class LoadShedderMiddleware:
    """
    Rejects requests when active connections exceed a threshold.
    Works for Django + DRF + Async/Sync endpoints.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _ACTIVE_REQUESTS

        with _LOCK:  # thread-safe access
            max_allowed = get_max_active_requests()
            if _ACTIVE_REQUESTS >= max_allowed:
                return JsonResponse(
                    {
                        "error": "Server overloaded",
                        "active": _ACTIVE_REQUESTS,
                        "max_allowed": max_allowed,
                    },
                    status=503,
                )

            _ACTIVE_REQUESTS += 1

        try:
            # Main request
            response = self.get_response(request)
            return response

        finally:
            # Decrement active request count safely
            with _LOCK:
                _ACTIVE_REQUESTS -= 1
