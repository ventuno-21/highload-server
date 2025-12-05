from prometheus_client import Counter, Histogram

API_REQUEST_COUNT = Counter(
    "api_request_count",
    "Total count of API requests",
    ["endpoint", "method"],
)

API_LATENCY = Histogram(
    "api_latency_seconds",
    "Latency of API endpoints",
    ["endpoint", "method"],
)

CACHE_HIT = Counter(
    "cache_hit_total",
    "Total cache hits",
    ["key"],
)

CACHE_MISS = Counter(
    "cache_miss_total",
    "Total cache misses",
    ["key"],
)
