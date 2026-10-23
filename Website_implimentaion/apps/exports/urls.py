from django.urls import path
from . import views

urlpatterns = [
    path('reports/downloads', views.downloads_view, name='downloads'),
    path('reports/schedules', views.schedules_view, name='schedules'),
    path('reports/downloads/<uuid:job_id>', views.download_file_view, name='download_file'),
    path('reports/downloads/<uuid:job_id>/retry', views.retry_job_view, name='retry_job'),
    path('api/exports/email', views.email_report_view, name='email_report'),
]
