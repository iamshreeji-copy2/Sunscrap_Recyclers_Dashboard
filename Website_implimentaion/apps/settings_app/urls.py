from django.urls import path
from . import views

urlpatterns = [
    path('settings/plant', views.plant_settings_view, name='plant_settings'),
    path('settings/devices', views.devices_settings_view, name='devices_settings'),
    path('settings/notifications', views.notifications_settings_view, name='notifications_settings'),
    path('settings/branding', views.branding_settings_view, name='branding_settings'),
    path('settings/system-health', views.system_health_view, name='system_health'),
    path('settings/audit', views.audit_view, name='audit_logs'),
    path('settings/users', views.users_settings_view, name='users_settings'),
]
