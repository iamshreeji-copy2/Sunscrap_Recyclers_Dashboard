from django.urls import path
from . import views

urlpatterns = [
    path('api/ingest/v1/batches', views.ingest_batch_view, name='ingest_batch'),
    path('api/devices/<str:device_id>/latest', views.device_latest_api, name='device_latest_api'),
    path('api/series', views.series_api, name='series_api'),
]
