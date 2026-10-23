from django.conf import settings
from django.utils import timezone
from apps.plant.models import Plant, Device, DeviceType

def plant_context(request):
    """Provides universal plant metadata and state to all templates."""
    plant = Plant.objects.first()
    data_source = getattr(settings, 'DATA_SOURCE', 'demo')
    
    total_devices = Device.objects.count()
    inv_count = Device.objects.filter(device_type=DeviceType.INVERTER).count()
    mfm_count = Device.objects.filter(device_type=DeviceType.MFM).count()
    wms_count = Device.objects.filter(device_type=DeviceType.WMS).count()
    
    return {
        'PLANT_ORGANIZATION': getattr(settings, 'PLANT_ORGANIZATION', 'SAT Solutions (SATs)'),
        'PLANT_NAME': getattr(settings, 'PLANT_NAME', 'SATs Solar Plant'),
        'PLANT_WEBSITE': getattr(settings, 'PLANT_WEBSITE', 'https://satsolutions.in/'),
        'PLANT_EMAIL': getattr(settings, 'PLANT_EMAIL', 'info.sats123@gmail.com'),
        'PLANT_AC_CAPACITY_KW': getattr(settings, 'PLANT_AC_CAPACITY_KW', 3900.0),
        'PLANT_DC_CAPACITY_KWP': getattr(settings, 'PLANT_DC_CAPACITY_KWP', 4640.0),
        'PLANT_TIMEZONE': getattr(settings, 'PLANT_TIMEZONE', 'Asia/Kolkata'),
        'DATA_SOURCE': data_source,
        'IS_DEMO': data_source.lower() == 'demo',
        'CURRENT_TIME': timezone.now(),
        'DEVICE_COUNTS': {
            'total': total_devices,
            'inverters': inv_count,
            'mfms': mfm_count,
            'wms': wms_count,
        }
    }
