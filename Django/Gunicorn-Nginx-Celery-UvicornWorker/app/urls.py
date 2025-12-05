from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("drf/sync-get/", views.DRFSyncGetAPI.as_view()),
    path("drf/sync-post/", views.DRFSyncPostAPI.as_view()),
    path("drf/async-post/", views.drf_async_post_view),
    # =======================================================
    path("json/async-get/", views.json_async_get_view),
    path("json/async-post/", views.json_async_post_view),
    path("json/sync-get/", views.json_sync_get_view),
    path("json/sync-post-celery/", views.json_sync_post_with_celery),
    path("json/sync-post/", csrf_exempt(views.JsonSyncPostView.as_view())),
    path("json/sync-get-mongo-data/", views.MongoEventsView.as_view()),
    # =======================================================
    path("check/", views.check),
    path("health/", views.health),
]
