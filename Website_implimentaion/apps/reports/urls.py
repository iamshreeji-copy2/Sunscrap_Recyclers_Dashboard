from django.urls import path
from . import views

urlpatterns = [
    path('reports/summary', views.report_summary_view, name='report_summary'),
    path('reports/energy/generation', views.report_energy_generation_view, name='report_energy_generation'),
    path('reports/inverter/generation', views.report_inverter_generation_view, name='report_inverter_generation'),
    path('reports/alarm', views.report_alarm_view, name='report_alarm'),
    path('reports/trends', views.report_trends_view, name='report_trends'),
    path('reports/custom-report', views.report_custom_view, name='report_custom'),
    path('reports/inverter/parameter', views.report_inverter_parameter_view, name='report_inverter_parameter'),
    path('reports/mfm/parameter', views.report_mfm_parameter_view, name='report_mfm_parameter'),
    path('reports/wms/parameter', views.report_wms_parameter_view, name='report_wms_parameter'),
    path('reports/communication', views.report_communication_view, name='report_communication'),
]
