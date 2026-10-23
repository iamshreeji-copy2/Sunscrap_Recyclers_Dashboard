from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('home', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('dashboard', views.dashboard_view, name='dashboard'),
    path('dashboard/analytical', views.dashboard_analytical_view, name='dashboard_analytical'),
    path('inverters/overview', views.inverter_overview_view, name='inverter_overview'),
    path('mfm/overview', views.mfm_overview_view, name='mfm_overview'),
    path('api/dashboard', views.api_dashboard_view, name='api_dashboard'),
]
