import shutil
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from apps.plant.models import Plant, Device, DeviceType
from apps.accounts.models import AuditLog

@login_required
def plant_settings_view(request):
    plant = Plant.objects.first()
    if request.method == 'POST':
        if not request.user.is_admin:
            messages.error(request, "Permission denied: Administrator role required.")
            return redirect('plant_settings')
            
        plant.name = request.POST.get('name', plant.name)
        plant.organization = request.POST.get('organization', plant.organization)
        plant.ac_capacity_kw = float(request.POST.get('ac_capacity_kw', plant.ac_capacity_kw))
        plant.dc_capacity_kwp = float(request.POST.get('dc_capacity_kwp', plant.dc_capacity_kwp))
        plant.expected_daily_yield_kwh = float(request.POST.get('expected_daily_yield_kwh', plant.expected_daily_yield_kwh))
        plant.timezone = request.POST.get('timezone', plant.timezone)
        plant.save()
        
        AuditLog.objects.create(
            user=request.user,
            action="UPDATE_PLANT_CONFIG",
            details="Updated plant capacities and topology configuration"
        )
        messages.success(request, "Plant configuration updated successfully.")
        return redirect('plant_settings')
        
    return render(request, 'settings/plant_settings.html', {'plant': plant})


@login_required
def devices_settings_view(request):
    devices = Device.objects.all().order_by('display_order', 'device_id')
    return render(request, 'settings/devices_settings.html', {'devices': devices})


@login_required
def notifications_settings_view(request):
    return render(request, 'settings/notifications_settings.html', {
        'smtp_configured': bool(getattr(settings, 'EMAIL_HOST', False)),
        'email_backend': getattr(settings, 'EMAIL_BACKEND', 'File/Local Mailbox')
    })


@login_required
def branding_settings_view(request):
    return render(request, 'settings/branding_settings.html')


@login_required
def system_health_view(request):
    # Disk usage
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (2**30), 2)
    total_gb = round(total / (2**30), 2)
    used_pct = round((used / total) * 100, 1)
    
    # DB stats
    device_count = Device.objects.count()
    
    health_data = {
        'status': 'HEALTHY',
        'database': 'Operational (SQLite / PostgreSQL ready)',
        'disk_free_gb': free_gb,
        'disk_total_gb': total_gb,
        'disk_used_pct': used_pct,
        'total_devices': device_count,
        'timezone': getattr(settings, 'PLANT_TIMEZONE', 'Asia/Kolkata'),
        'data_source': getattr(settings, 'DATA_SOURCE', 'demo'),
    }
    return render(request, 'settings/system_health.html', {'health': health_data})


@login_required
def audit_view(request):
    logs = AuditLog.objects.all().order_by('-timestamp')[:100]
    return render(request, 'settings/audit.html', {'logs': logs})
