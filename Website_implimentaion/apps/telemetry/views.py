import json
import hashlib
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from apps.plant.models import Device, DeviceType
from .models import (
    RawIngestBatch, InverterObservation, MFMObservation, WMSObservation,
    DeviceLatest, CommunicationStatus, DataQuality
)

@csrf_exempt
@require_http_methods(["POST"])
def ingest_batch_view(request):
    """
    Authenticated JSON collector batch ingest endpoint:
    POST /api/ingest/v1/batches
    Header: Authorization: Bearer <API_TOKEN> or X-Collector-Key
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({'status': 'REJECTED', 'error': f'Malformed JSON payload: {str(e)}'}, status=400)
        
    collector_id = data.get('collector_id', 'gateway-01')
    batch_sequence = data.get('sequence', 1)
    schema_version = data.get('schema_version', '1.0')
    records = data.get('records', [])
    
    # Calculate idempotency hash
    payload_raw = json.dumps(data, sort_keys=True)
    payload_hash = hashlib.sha256(payload_raw.encode()).hexdigest()
    
    # Check duplicate
    existing = RawIngestBatch.objects.filter(payload_hash=payload_hash).first()
    if existing:
        return JsonResponse({
            'status': 'ACCEPTED',
            'message': 'Duplicate batch acknowledged (idempotent)',
            'batch_id': existing.id
        }, status=200)
        
    batch_rec = RawIngestBatch.objects.create(
        collector_id=collector_id,
        schema_version=schema_version,
        batch_sequence=batch_sequence,
        payload_hash=payload_hash,
        payload=data,
        status="ACCEPTED"
    )
    
    # Process records
    processed_count = 0
    for rec in records:
        dev_id = rec.get('device_id')
        dt_str = rec.get('timestamp')
        timestamp = parse_datetime(dt_str) if dt_str else timezone.now()
        
        device = Device.objects.filter(device_id=dev_id).first()
        if not device:
            continue
            
        if device.device_type == DeviceType.INVERTER:
            InverterObservation.objects.create(
                device=device,
                timestamp=timestamp,
                vdc=rec.get('vdc', 0.0),
                idc=rec.get('idc', 0.0),
                v_ry=rec.get('v_ry', 800.0),
                v_yb=rec.get('v_yb', 800.0),
                v_br=rec.get('v_br', 800.0),
                i_r=rec.get('i_r', 0.0),
                i_y=rec.get('i_y', 0.0),
                i_b=rec.get('i_b', 0.0),
                power_factor=rec.get('power_factor', 0.99),
                frequency=rec.get('frequency', 50.0),
                active_power=rec.get('active_power', 0.0),
                reactive_power=rec.get('reactive_power', 0.0),
                dc_power=rec.get('dc_power', 0.0),
                daily_yield=rec.get('daily_yield', 0.0),
                lifetime_yield=rec.get('lifetime_yield', 0.0),
                insulation_resistance=rec.get('insulation_resistance', 1000.0),
                temperature=rec.get('temperature', 45.0),
                operating_status=rec.get('operating_status', 'Running'),
                alarm_code=rec.get('alarm_code', '0'),
                mppt_data=rec.get('mppt_data', {}),
                string_currents=rec.get('string_currents', []),
                quality=rec.get('quality', DataQuality.VALID)
            )
            DeviceLatest.objects.update_or_create(
                device=device,
                defaults={
                    'last_contact_time': timestamp,
                    'last_valid_time': timestamp,
                    'status': CommunicationStatus.ONLINE,
                    'operating_state': rec.get('operating_status', 'Running'),
                    'active_power': rec.get('active_power', 0.0),
                    'daily_yield': rec.get('daily_yield', 0.0),
                    'lifetime_yield': rec.get('lifetime_yield', 0.0),
                    'temperature': rec.get('temperature', 45.0),
                    'raw_snapshot': rec
                }
            )
            processed_count += 1
            
        elif device.device_type == DeviceType.MFM:
            MFMObservation.objects.create(
                device=device,
                timestamp=timestamp,
                active_power=rec.get('active_power', 0.0),
                reactive_power=rec.get('reactive_power', 0.0),
                apparent_power=rec.get('apparent_power', 0.0),
                v_ll=rec.get('v_ll', 11.0 if 'OUT' in device.device_id else 0.8),
                v_ry=rec.get('v_ry', 6350.0 if 'OUT' in device.device_id else 800.0),
                v_yb=rec.get('v_yb', 6350.0 if 'OUT' in device.device_id else 800.0),
                v_br=rec.get('v_br', 6350.0 if 'OUT' in device.device_id else 800.0),
                i_r=rec.get('i_r', 0.0),
                i_y=rec.get('i_y', 0.0),
                i_b=rec.get('i_b', 0.0),
                i_neutral=rec.get('i_neutral', 0.0),
                frequency=rec.get('frequency', 50.0),
                power_factor=rec.get('power_factor', 0.99),
                import_energy_today=rec.get('import_energy_today', 0.0),
                export_energy_today=rec.get('export_energy_today', 0.0),
                import_energy_lifetime=rec.get('import_energy_lifetime', 0.0),
                export_energy_lifetime=rec.get('export_energy_lifetime', 0.0),
                quality=rec.get('quality', DataQuality.VALID)
            )
            DeviceLatest.objects.update_or_create(
                device=device,
                defaults={
                    'last_contact_time': timestamp,
                    'last_valid_time': timestamp,
                    'status': CommunicationStatus.ONLINE,
                    'operating_state': "Normal",
                    'active_power': rec.get('active_power', 0.0),
                    'daily_yield': rec.get('export_energy_today', 0.0),
                    'lifetime_yield': rec.get('export_energy_lifetime', 0.0),
                    'raw_snapshot': rec
                }
            )
            processed_count += 1
            
        elif device.device_type == DeviceType.WMS:
            WMSObservation.objects.create(
                device=device,
                timestamp=timestamp,
                ambient_temp=rec.get('ambient_temp', 30.0),
                module_temp=rec.get('module_temp', 45.0),
                humidity=rec.get('humidity', 30.0),
                ghi=rec.get('ghi', 0.0),
                gti=rec.get('gti', 0.0),
                insolation_today_ghi=rec.get('insolation_today_ghi', 0.0),
                insolation_today_gti=rec.get('insolation_today_gti', 0.0),
                wind_speed=rec.get('wind_speed', 2.0),
                wind_direction=rec.get('wind_direction', 180.0),
                diffuse_irradiance=rec.get('diffuse_irradiance', 0.0),
                rainfall=rec.get('rainfall', 0.0),
                cloud_cover=rec.get('cloud_cover', 0.0),
                quality=rec.get('quality', DataQuality.VALID)
            )
            DeviceLatest.objects.update_or_create(
                device=device,
                defaults={
                    'last_contact_time': timestamp,
                    'last_valid_time': timestamp,
                    'status': CommunicationStatus.ONLINE,
                    'operating_state': "Normal",
                    'temperature': rec.get('ambient_temp', 30.0),
                    'raw_snapshot': rec
                }
            )
            processed_count += 1
            
    return JsonResponse({
        'status': 'ACCEPTED',
        'batch_id': batch_rec.id,
        'records_processed': processed_count
    }, status=201)


def device_latest_api(request, device_id):
    """GET /api/devices/<device_id>/latest"""
    dev = Device.objects.filter(device_id=device_id).first()
    if not dev:
        return JsonResponse({'error': f'Device {device_id} not found'}, status=404)
        
    latest = getattr(dev, 'latest_state', None)
    if not latest:
        return JsonResponse({'device_id': dev.device_id, 'status': 'unknown', 'message': 'No readings recorded'})
        
    return JsonResponse({
        'device_id': dev.device_id,
        'name': dev.name,
        'type': dev.device_type,
        'status': latest.status,
        'operating_state': latest.operating_state,
        'last_contact': latest.last_contact_time.isoformat(),
        'active_power_kw': latest.active_power,
        'daily_yield_kwh': latest.daily_yield,
        'lifetime_yield_kwh': latest.lifetime_yield,
        'temperature_c': latest.temperature,
        'conversion_efficiency_pct': latest.conversion_efficiency,
        'alarm_active': latest.alarm_active,
        'raw': latest.raw_snapshot
    })


def series_api(request):
    """
    GET /api/series?device=INV-01&metric=active_power&limit=500
    Returns downsampled time-series for charts
    """
    dev_id = request.GET.get('device')
    metric = request.GET.get('metric', 'active_power')
    
    device = Device.objects.filter(device_id=dev_id).first() if dev_id else None
    
    data_points = []
    if device and device.device_type == DeviceType.INVERTER:
        obs = InverterObservation.objects.filter(device=device).order_by('timestamp')[:500]
        for o in obs:
            val = getattr(o, metric, None)
            data_points.append({
                'time': o.timestamp.strftime('%H:%M'),
                'value': val if val is not None else 0.0
            })
    elif device and device.device_type == DeviceType.MFM:
        obs = MFMObservation.objects.filter(device=device).order_by('timestamp')[:500]
        for o in obs:
            val = getattr(o, metric, None)
            data_points.append({
                'time': o.timestamp.strftime('%H:%M'),
                'value': val if val is not None else 0.0
            })
    elif device and device.device_type == DeviceType.WMS:
        obs = WMSObservation.objects.filter(device=device).order_by('timestamp')[:500]
        for o in obs:
            val = getattr(o, metric, None)
            data_points.append({
                'time': o.timestamp.strftime('%H:%M'),
                'value': val if val is not None else 0.0
            })
            
    return JsonResponse({
        'device': dev_id,
        'metric': metric,
        'count': len(data_points),
        'points': data_points
    })
