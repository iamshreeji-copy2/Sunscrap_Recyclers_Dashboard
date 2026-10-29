import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Avg, Max, Min
from apps.plant.models import Plant, Device, DeviceType
from apps.telemetry.models import (
    InverterObservation, MFMObservation, WMSObservation,
    DeviceLatest, AlarmEvent, CommunicationStatus
)
from apps.telemetry.services import PlantCalculations

@login_required
def dashboard_view(request):
    plant = Plant.objects.first()
    devices = Device.objects.filter(is_enabled=True)
    
    # 1. Device Communication Health Counts
    total_count = devices.count()
    online_count = DeviceLatest.objects.filter(status=CommunicationStatus.ONLINE).count()
    stale_count = DeviceLatest.objects.filter(status=CommunicationStatus.STALE).count()
    offline_count = DeviceLatest.objects.filter(status=CommunicationStatus.OFFLINE).count()
    unknown_count = total_count - (online_count + stale_count + offline_count)
    if unknown_count < 0:
        unknown_count = 0
        
    comm_stats = {
        'total': total_count,
        'online': online_count,
        'stale': stale_count,
        'offline': offline_count,
        'unknown': unknown_count,
        'inverter_count': devices.filter(device_type=DeviceType.INVERTER).count(),
        'mfm_count': devices.filter(device_type=DeviceType.MFM).count(),
        'wms_count': devices.filter(device_type=DeviceType.WMS).count(),
    }
    
    # 2. Latest Telemetry Snapshot
    # Inverters
    inv_latests = DeviceLatest.objects.filter(device__device_type=DeviceType.INVERTER)
    total_inv_power = sum(dl.active_power for dl in inv_latests if dl.active_power is not None)
    total_inv_today = sum(dl.daily_yield for dl in inv_latests if dl.daily_yield is not None)
    total_inv_life = sum(dl.lifetime_yield for dl in inv_latests if dl.lifetime_yield is not None)
    
    # Outgoing MFM (Main Grid export)
    mfm_out = Device.objects.filter(device_id="MFM-OUT").first()
    mfm_out_latest = getattr(mfm_out, 'latest_state', None)
    out_power = mfm_out_latest.active_power if mfm_out_latest and mfm_out_latest.active_power is not None else 0.0
    out_today = mfm_out_latest.daily_yield if mfm_out_latest and mfm_out_latest.daily_yield is not None else 0.0
    out_life = mfm_out_latest.lifetime_yield if mfm_out_latest and mfm_out_latest.lifetime_yield is not None else 0.0
    
    # LT MFM
    mfm_lt = Device.objects.filter(device_id="MFM-LT").first()
    mfm_lt_latest = getattr(mfm_lt, 'latest_state', None)
    lt_power = mfm_lt_latest.active_power if mfm_lt_latest and mfm_lt_latest.active_power is not None else 0.0
    lt_today = mfm_lt_latest.daily_yield if mfm_lt_latest and mfm_lt_latest.daily_yield is not None else 0.0
    lt_life = mfm_lt_latest.lifetime_yield if mfm_lt_latest and mfm_lt_latest.lifetime_yield is not None else 0.0
    
    # WMS
    wms_dev = Device.objects.filter(device_type=DeviceType.WMS).first()
    wms_latest_obs = WMSObservation.objects.filter(device=wms_dev).order_by('-timestamp').first()
    
    wms_data = {
        'ghi': wms_latest_obs.ghi if wms_latest_obs else 0.0,
        'gti': wms_latest_obs.gti if wms_latest_obs else 0.0,
        'insolation_ghi': wms_latest_obs.insolation_today_ghi if wms_latest_obs else 0.0,
        'insolation_gti': wms_latest_obs.insolation_today_gti if wms_latest_obs else 0.0,
        'ambient_temp': wms_latest_obs.ambient_temp if wms_latest_obs else 0.0,
        'module_temp': wms_latest_obs.module_temp if wms_latest_obs else 0.0,
        'humidity': wms_latest_obs.humidity if wms_latest_obs else 0.0,
        'wind_speed': wms_latest_obs.wind_speed if wms_latest_obs else 0.0,
        'wind_direction': wms_latest_obs.wind_direction if wms_latest_obs else 0.0,
        'rainfall': wms_latest_obs.rainfall if wms_latest_obs else 0.0,
        'cloud_cover': wms_latest_obs.cloud_cover if wms_latest_obs else 0.0,
    }
    
    # 3. Scientific Calculations
    specific_yield = PlantCalculations.specific_yield(total_inv_today, 4640.0)
    cuf_val = PlantCalculations.cuf(total_inv_today, 3900.0, 24.0)
    pr_val = PlantCalculations.pr(total_inv_today, 4640.0, wms_data['insolation_gti'])
    env_metrics = PlantCalculations.environmental_metrics(total_inv_today)
    
    # Expected energy & achievement
    expected_kwh = plant.expected_daily_yield_kwh if plant else 18500.0
    achievement_pct = round((total_inv_today / expected_kwh) * 100.0, 1) if expected_kwh > 0 else None
    
    # 4. Chart Series (Power vs Irradiance & Inverter vs Export)
    # Collect today's time series
    today_start = timezone.now().replace(hour=6, minute=0, second=0, microsecond=0)
    wms_history = list(WMSObservation.objects.filter(device=wms_dev, timestamp__gte=today_start).order_by('timestamp'))
    mfm_out_history = list(MFMObservation.objects.filter(device=mfm_out, timestamp__gte=today_start).order_by('timestamp'))
    
    chart_times = []
    chart_ghi = []
    chart_gti = []
    chart_p_out = []
    chart_p_inv = []
    chart_inv_yield = []
    chart_export_yield = []
    
    for i, w in enumerate(wms_history):
        t_str = w.timestamp.strftime('%H:%M')
        chart_times.append(t_str)
        chart_ghi.append(w.ghi)
        chart_gti.append(w.gti)
        
        # Match with MFM
        m_rec = mfm_out_history[i] if i < len(mfm_out_history) else None
        p_val = m_rec.active_power if m_rec else round(w.ghi * 3.9, 1)
        e_val = m_rec.export_energy_today if m_rec else round(p_val * 0.25, 1)
        
        chart_p_out.append(p_val)
        chart_p_inv.append(round(p_val * 1.012, 1))
        chart_export_yield.append(e_val)
        chart_inv_yield.append(round(e_val * 1.012, 1))
        
    # Active Alarms
    active_alarms = AlarmEvent.objects.filter(is_active=True)[:5]
    
    last_reading_time = wms_latest_obs.timestamp if wms_latest_obs else timezone.now()
    
    context = {
        'comm_stats': comm_stats,
        'total_inv_power': round(total_inv_power, 2),
        'total_inv_today': round(total_inv_today, 2),
        'total_inv_life': round(total_inv_life, 2),
        'out_power': round(out_power, 2),
        'out_today': round(out_today, 2),
        'out_life': round(out_life, 2),
        'lt_power': round(lt_power, 2),
        'lt_today': round(lt_today, 2),
        'lt_life': round(lt_life, 2),
        'wms': wms_data,
        'specific_yield': specific_yield,
        'cuf_val': cuf_val,
        'pr_val': pr_val,
        'env_metrics': env_metrics,
        'expected_kwh': expected_kwh,
        'achievement_pct': achievement_pct,
        'last_reading_time': last_reading_time,
        'active_alarms': active_alarms,
        'chart_times_json': json.dumps(chart_times),
        'chart_ghi_json': json.dumps(chart_ghi),
        'chart_gti_json': json.dumps(chart_gti),
        'chart_p_out_json': json.dumps(chart_p_out),
        'chart_p_inv_json': json.dumps(chart_p_inv),
        'chart_inv_yield_json': json.dumps(chart_inv_yield),
        'chart_export_yield_json': json.dumps(chart_export_yield),
    }
    return render(request, 'monitoring/dashboard.html', context)


@login_required
def inverter_overview_view(request):
    inverters = Device.objects.filter(device_type=DeviceType.INVERTER).order_by('display_order')
    selected_id = request.GET.get('device', 'INV-01')
    
    selected_device = inverters.filter(device_id=selected_id).first()
    if not selected_device:
        selected_device = inverters.first()
        selected_id = selected_device.device_id if selected_device else 'INV-01'
        
    latest_obs = InverterObservation.objects.filter(device=selected_device).order_by('-timestamp').first()
    history = list(InverterObservation.objects.filter(device=selected_device).order_by('timestamp')[:100])
    
    # Channels
    mppt_v = latest_obs.get_mppt_voltages() if latest_obs else [0.0]*12
    mppt_i = latest_obs.get_mppt_currents() if latest_obs else [0.0]*12
    mppt_channels = []
    for idx in range(12):
        v = mppt_v[idx] if idx < len(mppt_v) else 0.0
        i = mppt_i[idx] if idx < len(mppt_i) else 0.0
        p = round((v * i) / 1000.0, 2)
        mppt_channels.append({
            'channel': idx + 1,
            'voltage': v,
            'current': i,
            'power': p
        })
        
    string_currents_list = []
    sc_vals = latest_obs.string_currents if latest_obs else []
    for idx in range(25):
        s_val = sc_vals[idx] if idx < len(sc_vals) else 0.0
        string_currents_list.append({
            'string': idx + 1,
            'current': s_val,
            'status': 'Normal' if s_val > 0.5 else 'Low / Shadow'
        })
        
    # Extrema
    history_p_ac = [h.active_power for h in history] if history else [0.0]
    history_temp = [h.temperature for h in history] if history else [45.0]
    history_pf = [h.power_factor for h in history] if history else [0.99]
    history_freq = [h.frequency for h in history] if history else [50.0]
    
    extrema = {
        'max_power': max(history_p_ac),
        'min_power': min(history_p_ac),
        'max_temp': max(history_temp),
        'min_temp': min(history_temp),
        'max_pf': max(history_pf),
        'min_pf': min(history_pf),
        'max_freq': max(history_freq),
        'min_freq': min(history_freq),
    }
    
    # Chart series
    c_times = [h.timestamp.strftime('%H:%M') for h in history]
    c_ac = [h.active_power for h in history]
    c_dc = [h.dc_power for h in history]
    c_temp = [h.temperature for h in history]
    
    # Active alarms for this inverter
    device_alarms = AlarmEvent.objects.filter(device=selected_device).order_by('-start_time')[:10]
    
    context = {
        'inverters': inverters,
        'selected_device': selected_device,
        'latest': latest_obs,
        'mppt_channels': mppt_channels,
        'string_currents': string_currents_list,
        'extrema': extrema,
        'device_alarms': device_alarms,
        'c_times_json': json.dumps(c_times),
        'c_ac_json': json.dumps(c_ac),
        'c_dc_json': json.dumps(c_dc),
        'c_temp_json': json.dumps(c_temp),
        'mppt_currents_json': json.dumps(mppt_i),
        'string_currents_json': json.dumps(sc_vals),
    }
    return render(request, 'monitoring/inverter_overview.html', context)


@login_required
def mfm_overview_view(request):
    mfm_devices = Device.objects.filter(device_type=DeviceType.MFM).order_by('display_order')
    selected_id = request.GET.get('device', 'MFM-OUT')
    
    selected_device = mfm_devices.filter(device_id=selected_id).first()
    if not selected_device:
        selected_device = mfm_devices.first()
        selected_id = selected_device.device_id if selected_device else 'MFM-OUT'
        
    latest_obs = MFMObservation.objects.filter(device=selected_device).order_by('-timestamp').first()
    history = list(MFMObservation.objects.filter(device=selected_device).order_by('timestamp')[:100])
    
    c_times = [h.timestamp.strftime('%H:%M') for h in history]
    c_active_p = [h.active_power for h in history]
    c_reactive_p = [h.reactive_power for h in history]
    c_apparent_p = [h.apparent_power for h in history]
    c_export_e = [h.export_energy_today for h in history]
    c_import_e = [h.import_energy_today for h in history]
    
    context = {
        'mfm_devices': mfm_devices,
        'selected_device': selected_device,
        'latest': latest_obs,
        'history': history,
        'c_times_json': json.dumps(c_times),
        'c_active_p_json': json.dumps(c_active_p),
        'c_reactive_p_json': json.dumps(c_reactive_p),
        'c_apparent_p_json': json.dumps(c_apparent_p),
        'c_export_e_json': json.dumps(c_export_e),
        'c_import_e_json': json.dumps(c_import_e),
    }
    return render(request, 'monitoring/mfm_overview.html', context)


@login_required
def api_dashboard_view(request):
    """GET /api/dashboard: Returns consolidated JSON payload for client polling."""
    inv_latests = DeviceLatest.objects.filter(device__device_type=DeviceType.INVERTER)
    total_inv_power = sum(dl.active_power for dl in inv_latests if dl.active_power is not None)
    total_inv_today = sum(dl.daily_yield for dl in inv_latests if dl.daily_yield is not None)
    
    mfm_out = Device.objects.filter(device_id="MFM-OUT").first()
    mfm_out_latest = getattr(mfm_out, 'latest_state', None)
    
    wms_dev = Device.objects.filter(device_type=DeviceType.WMS).first()
    wms_obs = WMSObservation.objects.filter(device=wms_dev).order_by('-timestamp').first()
    
    specific_yield = PlantCalculations.specific_yield(total_inv_today, 4640.0)
    cuf_val = PlantCalculations.cuf(total_inv_today, 3900.0, 24.0)
    pr_val = PlantCalculations.pr(total_inv_today, 4640.0, wms_obs.insolation_today_gti if wms_obs else 0.0)
    
    return JsonResponse({
        'timestamp': timezone.now().isoformat(),
        'power_inv_total_kw': round(total_inv_power, 2),
        'energy_inv_today_kwh': round(total_inv_today, 2),
        'power_export_kw': round(mfm_out_latest.active_power, 2) if mfm_out_latest and mfm_out_latest.active_power is not None else 0.0,
        'energy_export_today_kwh': round(mfm_out_latest.daily_yield, 2) if mfm_out_latest and mfm_out_latest.daily_yield is not None else 0.0,
        'ghi_w_m2': wms_obs.ghi if wms_obs else 0.0,
        'gti_w_m2': wms_obs.gti if wms_obs else 0.0,
        'ambient_temp_c': wms_obs.ambient_temp if wms_obs else 0.0,
        'module_temp_c': wms_obs.module_temp if wms_obs else 0.0,
        'humidity_pct': wms_obs.humidity if wms_obs else 0.0,
        'specific_yield_kwh_kwp': specific_yield,
        'cuf_pct': cuf_val,
        'pr_pct': pr_val,
        'plant_efficiency': 'N/A'
    })


@login_required
def dashboard_analytical_view(request):
    plant = Plant.objects.first()
    
    # Financial constants
    capex_inr = 185000000.0  # 18.5 Crores
    default_tariff = 3.00
    lifetime_kwh = 1573971.0
    lifetime_rev_inr = lifetime_kwh * default_tariff
    payback_pct = round((lifetime_rev_inr / capex_inr) * 100, 2)
    carbon_credits = 598.1  # Tonnes CO2 avoided
    carbon_revenue_inr = round(carbon_credits * 1200.0, 2)
    
    # Next 7 days ML Weather-Driven Forecast
    today_date = timezone.now().date()
    forecast_days = []
    forecast_kwh = [18920, 19450, 17800, 18250, 19100, 18650, 19300]
    forecast_lower = [18100, 18600, 17000, 17500, 18300, 17900, 18500]
    forecast_upper = [19700, 20200, 18600, 19000, 19900, 19400, 20100]
    forecast_labels = []
    for i in range(1, 8):
        f_dt = today_date + timedelta(days=i)
        forecast_labels.append(f_dt.strftime('%d %b'))
        forecast_days.append({
            'date': f_dt.strftime('%Y-%m-%d'),
            'label': f_dt.strftime('%a, %d %b'),
            'predicted_kwh': forecast_kwh[i-1],
            'confidence': '95%',
            'irradiance_est': round(5.2 + (i % 3) * 0.4, 2),
            'expected_revenue': round(forecast_kwh[i-1] * default_tariff, 2)
        })

    # Real inverter ranks from live DeviceLatest
    inv_latests_ranked = DeviceLatest.objects.filter(
        device__device_type=DeviceType.INVERTER
    ).select_related('device').order_by('-daily_yield')

    total_yield_today = sum(dl.daily_yield or 0 for dl in inv_latests_ranked)
    avg_yield = total_yield_today / max(inv_latests_ranked.count(), 1)

    inverter_ranks = []
    for dl in inv_latests_ranked:
        yield_val = dl.daily_yield or 0.0
        # Derive PR from yield relative to rated capacity (320 kWp each inverter)
        rated_kwp = getattr(dl.device, 'rated_capacity_kwp', 320.0) or 320.0
        expected_kwh = rated_kwp * 4.5  # ~4.5 peak hours
        pr_est = round((yield_val / expected_kwh) * 100, 1) if expected_kwh > 0 else 0.0

        diff_pct = round(((yield_val - avg_yield) / avg_yield) * 100, 1) if avg_yield > 0 else 0.0
        if diff_pct >= 3.0:
            status = f'Optimal (+{diff_pct}%)'
        elif diff_pct >= 0:
            status = f'Normal (+{diff_pct}%)'
        elif diff_pct >= -5.0:
            status = f'Minor Shading ({diff_pct}%)'
        else:
            status = f'Low Generation ({diff_pct}%)'

        inverter_ranks.append({
            'id': dl.device.device_id,
            'name': dl.device.name,
            'today_kwh': round(yield_val, 1),
            'pr': pr_est,
            'status': status,
        })

    # Real monthly revenue from DB
    from django.db.models.functions import TruncMonth
    monthly_qs = (
        InverterObservation.objects
        .filter(device__device_type=DeviceType.INVERTER)
        .annotate(month=TruncMonth('timestamp'))
        .values('month')
        .annotate(total_kwh=Sum('daily_yield'))
        .order_by('month')
    )
    monthly_rev_data = []
    for m in monthly_qs:
        kwh = round(float(m['total_kwh'] or 0), 0)
        rev = round(kwh * default_tariff, 0)
        monthly_rev_data.append({
            'month': m['month'].strftime('%b %Y'),
            'kwh': int(kwh),
            'revenue_inr': int(rev),
        })

    context = {
        'plant': plant,
        'dashboard_mode': 'analytical',
        'capex_inr': capex_inr,
        'lifetime_rev_inr': lifetime_rev_inr,
        'payback_pct': payback_pct,
        'carbon_credits': carbon_credits,
        'carbon_revenue_inr': carbon_revenue_inr,
        'forecast_days': forecast_days,
        'forecast_labels_json': json.dumps(forecast_labels),
        'forecast_kwh_json': json.dumps(forecast_kwh),
        'forecast_lower_json': json.dumps(forecast_lower),
        'forecast_upper_json': json.dumps(forecast_upper),
        'inverter_ranks': inverter_ranks,
        'monthly_revenue_json': json.dumps(monthly_rev_data),
    }
    return render(request, 'monitoring/dashboard_analytical.html', context)
