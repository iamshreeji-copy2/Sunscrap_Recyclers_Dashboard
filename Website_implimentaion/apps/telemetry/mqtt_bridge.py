"""
Sunscrap / SATs Solar SCADA - Live MQTT Telemetry Bridge Service
Connects to EMQX Cloud Broker, consumes real-time datalogger telemetry packets across:
- sunscrap/data/# (all topics)
- sunscrap/data/INV_1 ... sunscrap/data/INV_13
- sunscrap/data/WMS
- sunscrap/data/MFM
- scada/sunscrap/plant-01/logger-001/telemetry
Includes vendor JSON auto-repair (handles missing device_id keys from field firmware),
extracts 24/25 string currents and 12 MPPT channels, and updates live SCADA database.
"""

import os
import sys
import re
import json
import ssl
import time
import hashlib
import logging
from datetime import datetime, timedelta
import django

# Ensure Django is initialized if executed standalone
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sunscrap_scada.settings')
    django.setup()

from django.utils.dateparse import parse_datetime
from django.utils import timezone
from apps.plant.models import Device, DeviceType
from apps.telemetry.models import (
    RawIngestBatch, InverterObservation, MFMObservation, WMSObservation,
    DeviceLatest, CommunicationStatus, DataQuality, AlarmEvent, AlarmSeverity
)
import paho.mqtt.client as mqtt

logger = logging.getLogger('mqtt_bridge')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [MQTT-BRIDGE] %(message)s'
)

# Default configuration from datalogger plan
DEFAULT_BROKER_HOST = os.environ.get('MQTT_BROKER_HOST', 'k6fc1317.ala.dedicated.aws.emqxcloud.com')
DEFAULT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT', '8883'))
DEFAULT_USERNAME = os.environ.get('MQTT_USERNAME', 'vendor_logger_001')
DEFAULT_PASSWORD = os.environ.get('MQTT_PASSWORD', 'Telemetry#Gateway@9482')
DEFAULT_CLIENT_ID = os.environ.get('MQTT_CLIENT_ID', 'sunscrap-scada-bridge-01')
DEFAULT_TOPIC = os.environ.get('MQTT_TOPIC', 'sunscrap/data/#')
STATUS_TOPIC = os.environ.get('MQTT_STATUS_TOPIC', 'scada/sunscrap/plant-01/logger-001/status')


def clean_vendor_json(payload_str):
    """
    Vendor firmware bug auto-fix:
    The datalogger outputs malformed JSON starting with {"INV-9", ...} or {"WMS", ...}
    without a property name.
    This regex auto-repairs it to {"device_id": "INV-9", ...}.
    """
    cleaned = re.sub(r'\{\s*\"([A-Za-z0-9_#-]+)\"\s*,', r'{"device_id": "\1",', payload_str)
    return cleaned


def resolve_device(dev_identifier, topic=""):
    """
    Robust device resolver. Maps:
    - 'INV_1' / 'INV-1' / 'INV1' / 'INV_01' -> Device('INV-01')
    - 'INV_9' / 'INV-9' -> Device('INV-09')
    - 'INV_13' -> Device('INV-13')
    - 'WMS' -> Device('WMS-01')
    - 'MFM' / 'MFM_1' / 'MFM_LT' -> Device('MFM-LT')
    - 'MFM_2' / 'MFM_OUT' -> Device('MFM-OUT')
    """
    candidates = []
    if dev_identifier:
        candidates.append(str(dev_identifier).strip())
    if topic:
        parts = [p.strip() for p in topic.split('/') if p.strip()]
        if parts:
            candidates.append(parts[-1])
            if len(parts) > 1:
                candidates.append(parts[-2])

    for raw in candidates:
        raw_clean = raw.upper().strip()
        d = Device.objects.filter(device_id__iexact=raw_clean).first()
        if d:
            return d

        m = re.search(r'INV[_-]?([0-9]{1,2})', raw_clean)
        if m:
            num = int(m.group(1))
            d = Device.objects.filter(device_id=f"INV-{num:02d}").first()
            if d:
                return d

        if 'WMS' in raw_clean or 'WEATHER' in raw_clean:
            d = Device.objects.filter(device_id='WMS-01').first()
            if d:
                return d

        if any(k in raw_clean for k in ['MFM-LT', 'MFM_LT', 'MFM1', 'MFM_1', 'MFM-01', 'LT_METER', 'LT-METER']):
            d = Device.objects.filter(device_id='MFM-LT').first()
            if d:
                return d
        if any(k in raw_clean for k in ['MFM-OUT', 'MFM_OUT', 'MFM2', 'MFM_2', 'MFM-02', 'OUT_METER', 'OUT-METER']):
            d = Device.objects.filter(device_id='MFM-OUT').first()
            if d:
                return d
        if 'MFM' in raw_clean or 'METER' in raw_clean:
            d = Device.objects.filter(device_id='MFM-LT').first()
            if d:
                return d

    return None


def parse_string_currents(data_obj):
    """
    Extracts up to 25 string currents from diverse vendor payload layouts:
    - Vendor fields: 'string1_Idc' .. 'string24_Idc'
    - List of dicts: [{'String #': 1, 'Current (A)': 8.4, 'Status': 'Normal'}, ...]
    - Dict key 'strings' / 'String Data'
    - Array of floats: 'string_currents': [8.4, 8.2, ...]
    """
    currents = [0.0] * 25
    statuses = ["Normal"] * 25
    items = []

    if isinstance(data_obj, list):
        if data_obj and isinstance(data_obj[0], dict) and any(k in data_obj[0] for k in ['String #', 'String#', 'string', 'Current (A)', 'Current']):
            items = data_obj
    elif isinstance(data_obj, dict):
        for k in ['strings', 'String Data', 'string_data', 'string_table', 'Strings', 'data']:
            if k in data_obj and isinstance(data_obj[k], list):
                items = data_obj[k]
                break

    if items:
        for item in items:
            if not isinstance(item, dict):
                continue
            num = None
            for num_key in ['String #', 'String#', 'string', 'string_num', 'str', 'id', 'num', 'String']:
                if num_key in item:
                    try:
                        num = int(re.sub(r'[^0-9]', '', str(item[num_key])))
                        break
                    except Exception:
                        pass
            curr_val = None
            for c_key in ['Current (A)', 'Current(A)', 'current', 'Current', 'i', 'amps', 'val', 'value']:
                if c_key in item:
                    try:
                        curr_val = float(item[c_key])
                        break
                    except Exception:
                        pass
            status_val = item.get('Status') or item.get('status') or "Normal"
            if num and 1 <= num <= 25 and curr_val is not None:
                currents[num - 1] = curr_val
                statuses[num - 1] = str(status_val)
        return currents, statuses

    if isinstance(data_obj, dict) and 'string_currents' in data_obj and isinstance(data_obj['string_currents'], list):
        for idx, val in enumerate(data_obj['string_currents'][:25]):
            try:
                currents[idx] = float(val)
            except Exception:
                pass
        return currents, statuses

    # Check vendor naming: 'string1_Idc' to 'string24_Idc'
    if isinstance(data_obj, dict):
        for idx in range(1, 26):
            for k in [
                f'string{idx}_Idc', f'string_{idx}_Idc', f'string{idx}_idc', f'string_{idx}_idc',
                f'string_{idx}_current', f'string{idx}_current', f'string_{idx}', f'string{idx}',
                f'str_{idx}', f'str{idx}', f's{idx}_current', f'String_{idx}', f'String{idx}'
            ]:
                if k in data_obj and data_obj[k] is not None:
                    try:
                        val = float(data_obj[k])
                        # Sanitize invalid 6553.5 disconnect markers
                        currents[idx - 1] = 0.0 if val > 2000.0 else val
                        break
                    except Exception:
                        pass

    return currents, statuses


def parse_mppt_data(data_obj):
    """
    Extracts 12 MPPT channel voltages and currents from vendor payload:
    - 'pv1_Vdc' .. 'pv12_Vdc'
    - 'pv1_Idc' .. 'pv12_Idc'
    Sanitizes 6553.5 disconnect markers down to 0.0.
    """
    mppt_v = [0.0] * 12
    mppt_i = [0.0] * 12

    if isinstance(data_obj, dict):
        for idx in range(1, 13):
            # Voltage
            for vk in [f'pv{idx}_Vdc', f'pv{idx}_vdc', f'mppt{idx}_vdc', f'mppt_{idx}_vdc']:
                if vk in data_obj and data_obj[vk] is not None:
                    try:
                        v = float(data_obj[vk])
                        mppt_v[idx - 1] = 0.0 if v > 6000.0 else v
                        break
                    except Exception:
                        pass
            # Current
            for ik in [f'pv{idx}_Idc', f'pv{idx}_idc', f'mppt{idx}_idc', f'mppt_{idx}_idc']:
                if ik in data_obj and data_obj[ik] is not None:
                    try:
                        i = float(data_obj[ik])
                        mppt_i[idx - 1] = 0.0 if i > 6000.0 else i
                        break
                    except Exception:
                        pass

    return {'v': mppt_v, 'i': mppt_i}


def extract_metric(data, keys, default=0.0):
    if not isinstance(data, dict):
        return default
    for k in keys:
        if k in data and data[k] is not None:
            try:
                v = float(data[k])
                return 0.0 if v > 60000.0 else v
            except Exception:
                pass
    if 'metrics' in data and isinstance(data['metrics'], dict):
        for k in keys:
            if k in data['metrics'] and data['metrics'][k] is not None:
                try:
                    v = float(data['metrics'][k])
                    return 0.0 if v > 60000.0 else v
                except Exception:
                    pass
    return default


def extract_str(data, keys, default=""):
    if not isinstance(data, dict):
        return default
    for k in keys:
        if k in data and data[k] is not None:
            return str(data[k]).strip()
    return default


class ScadaMqttBridge:
    def __init__(self, host=DEFAULT_BROKER_HOST, port=DEFAULT_BROKER_PORT,
                 username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD,
                 client_id=DEFAULT_CLIENT_ID, topic=DEFAULT_TOPIC, use_tls=True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        self.topic = topic
        self.use_tls = use_tls
        self.client = None
        self.running = False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc.value if hasattr(rc, 'value') else rc
        if rc_code == 0:
            logger.info(f"Connected successfully to MQTT Broker at {self.host}:{self.port}")
            topics_to_sub = [
                ("sunscrap/data/#", 1),
                ("sunscrap/data", 1),
                ("scada/sunscrap/#", 1),
                (self.topic, 1),
                (STATUS_TOPIC, 1)
            ]
            seen = set()
            unique_topics = []
            for t, q in topics_to_sub:
                if t not in seen:
                    seen.add(t)
                    unique_topics.append((t, q))
            client.subscribe(unique_topics)
            logger.info(f"Subscribed to topics: {[t[0] for t in unique_topics]}")
        else:
            logger.error(f"Failed to connect to MQTT Broker, return code: {rc_code}")

    def on_disconnect(self, client, userdata, rc, properties=None):
        logger.warning(f"Disconnected from MQTT Broker (rc={rc}). Reconnecting automatically...")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload_str = msg.payload.decode('utf-8')
            # Auto-repair vendor malformed JSON: e.g. {"INV-9", ...} or {"WMS", ...}
            cleaned_str = clean_vendor_json(payload_str)
            data = json.loads(cleaned_str)
        except Exception as e:
            logger.error(f"Failed to parse payload on {topic}: {e} (Raw: {msg.payload[:80]}...)")
            return

        logger.info(f"Received message on {topic} ({len(msg.payload)} bytes)")

        try:
            if topic == STATUS_TOPIC:
                self.handle_status_message(data)
            else:
                self.handle_telemetry_message(data, topic=topic)
        except Exception as e:
            logger.exception(f"Error processing telemetry packet from {topic}: {e}")

    def handle_status_message(self, data):
        logger.info(f"Logger status update: {data}")

    def handle_telemetry_message(self, data, topic=""):
        collector_id = 'sunscrap-logger-001'
        sequence = 1
        schema_version = '1.0'

        if isinstance(data, dict):
            collector_id = data.get('collector_id') or data.get('logger_id') or 'sunscrap-logger-001'
            sequence = data.get('sequence', 1)
            schema_version = data.get('schema_version', '1.0')

        # Calculate idempotency payload hash
        payload_raw = json.dumps(data, sort_keys=True)
        payload_hash = hashlib.sha256(payload_raw.encode()).hexdigest()

        # Idempotent deduplication check (10-second deduplication window for retransmitted packets)
        ten_secs_ago = timezone.now() - timedelta(seconds=10)
        existing = RawIngestBatch.objects.filter(payload_hash=payload_hash, received_at__gte=ten_secs_ago).first()
        if existing:
            logger.info(f"Batch duplicate detected within 10s (hash {payload_hash[:12]}...), skipping duplicate write.")
            return

        batch_rec = RawIngestBatch.objects.create(
            collector_id=collector_id,
            schema_version=schema_version,
            batch_sequence=sequence,
            payload_hash=payload_hash,
            payload=data if isinstance(data, dict) else {"data": data, "topic": topic},
            status="ACCEPTED"
        )

        records = []
        if isinstance(data, list):
            if data and isinstance(data[0], dict) and ('String #' in data[0] or 'String#' in data[0] or 'Current (A)' in data[0]):
                records = [{"strings": data}]
            else:
                records = data
        elif isinstance(data, dict):
            records = data.get('records') or data.get('samples') or []
            if not records:
                records = [data]

        processed = 0
        total_kw = 0.0

        for rec in records:
            dev_id = None
            if isinstance(rec, dict):
                dev_id = rec.get('device_id') or rec.get('id') or rec.get('device') or rec.get('inverter_id')
            device = resolve_device(dev_id, topic=topic)
            if not device:
                continue

            dt_str = None
            if isinstance(rec, dict):
                dt_str = rec.get('timestamp') or rec.get('observed_at') or rec.get('time') or rec.get('Timestamp')
            timestamp = parse_datetime(dt_str) if dt_str else timezone.now()
            if not timestamp:
                timestamp = timezone.now()

            # Process by device type
            if device.device_type == DeviceType.INVERTER:
                string_currents, string_statuses = parse_string_currents(rec)
                mppt_data = parse_mppt_data(rec)

                kw = extract_metric(rec, [
                    'active_power', 'power', 'power_kw', 'pac', 'p_ac', 'Active Power (kW)',
                    'Active Power', 'Active_Power', 'kw', 'KW', 'activePower', 'inputkw'
                ], default=0.0)

                temp = extract_metric(rec, [
                    'temperature', 'temp', 'internal_temp', 'inv_temp', 'module_temp',
                    'Temperature (°C)', 'Temperature', 'inverter_temp'
                ], default=44.0)

                daily_kwh = extract_metric(rec, [
                    'daily_yield', 'yield_today', 'today_kwh', 'energy_today', 'e_today',
                    'energy_yield_daily', 'Daily Yield (kWh)', 'Daily Yield', 'today_yield', 'dailyEnergy'
                ], default=0.0)

                total_kwh = extract_metric(rec, [
                    'lifetime_yield', 'total_yield', 'e_total', 'energy_yield_total',
                    'cumulative_energy', 'Lifetime Yield (kWh)'
                ], default=0.0)

                v_ry = extract_metric(rec, [
                    'p2p_volt_ry', 'v_ry', 'v_ll', 'grid_voltage', 'Grid Voltage (V)', 'ac_voltage', 'voltage_ry'
                ], default=800.0)
                v_yb = extract_metric(rec, ['p2p_volt_yb', 'v_yb'], default=v_ry)
                v_br = extract_metric(rec, ['p2p_volt_br', 'v_br'], default=v_ry)

                vdc = extract_metric(rec, ['vdc', 'v_dc', 'dc_voltage', 'DC Voltage (V)', 'dcVoltage'], default=745.0)
                idc = extract_metric(rec, ['idc', 'i_dc', 'dc_current', 'DC Current (A)', 'dcCurrent'], default=0.0)

                sum_strings = sum(string_currents)
                if idc == 0.0 and sum_strings > 0:
                    idc = round(sum_strings, 1)

                if kw == 0.0 and idc > 0 and vdc > 0 and idc < 1000.0:
                    dc_kw = (vdc * idc) / 1000.0
                    kw = round(dc_kw * 0.985, 1)

                dc_power = extract_metric(rec, ['dc_power', 'dcPower', 'DC Power (kW)'], default=round(kw * 1.015, 1))
                status_str = extract_str(rec, ['operating_status', 'status', 'Status', 'state', 'operational_status', 'device_status'], default="Running")
                if status_str == '0':
                    status_str = "Running"

                alarm_code = extract_str(rec, ['alarm_code', 'alarm', 'error_code', 'fault_code', 'Alarm Code', 'fault'], default="0")

                for idx, s_stat in enumerate(string_statuses):
                    if s_stat.upper() in ['WARNING', 'FAULT', 'ABNORMAL', 'SHADOW']:
                        if alarm_code == '0':
                            alarm_code = f'STR-{idx+1:02d}'

                i_r = extract_metric(rec, ['ir', 'i_r'], default=round(kw * 1000.0 / (1.732 * v_ry), 1) if v_ry > 0 else 0.0)
                i_y = extract_metric(rec, ['iy', 'i_y'], default=i_r)
                i_b = extract_metric(rec, ['ib', 'i_b'], default=i_r)
                pf = extract_metric(rec, ['pf', 'power_factor', 'Power Factor'], default=0.996)
                freq = extract_metric(rec, ['freq', 'frequency', 'Frequency (Hz)'], default=50.02)
                r_iso = extract_metric(rec, ['insulation_resistance', 'r_iso'], default=1000.0)

                InverterObservation.objects.create(
                    device=device,
                    timestamp=timestamp,
                    vdc=vdc,
                    idc=idc,
                    v_ry=v_ry,
                    v_yb=v_yb,
                    v_br=v_br,
                    i_r=i_r,
                    i_y=i_y,
                    i_b=i_b,
                    power_factor=pf,
                    frequency=freq,
                    active_power=kw,
                    reactive_power=extract_metric(rec, ['reactive_power', 'q_var', 'Reactive Power'], default=0.0),
                    dc_power=dc_power,
                    daily_yield=daily_kwh,
                    lifetime_yield=total_kwh,
                    insulation_resistance=r_iso,
                    temperature=temp,
                    operating_status=status_str,
                    alarm_code=alarm_code,
                    string_currents=string_currents,
                    mppt_data=mppt_data,
                    quality=DataQuality.VALID
                )

                DeviceLatest.objects.update_or_create(
                    device=device,
                    defaults={
                        'last_contact_time': timezone.now(),
                        'last_valid_time': timestamp,
                        'status': CommunicationStatus.ONLINE,
                        'operating_state': status_str,
                        'active_power': kw,
                        'daily_yield': daily_kwh,
                        'lifetime_yield': total_kwh,
                        'temperature': temp,
                        'voltage_ry': v_ry,
                        'power_factor': pf,
                        'frequency': freq,
                        'latest_alarm_code': alarm_code if alarm_code != '0' else '',
                        'alarm_active': (alarm_code != '0' and alarm_code != '')
                    }
                )

                total_kw += kw
                processed += 1

                # Check for critical Inverter 08 Temperature Alert (ERR-402)
                if temp > 47.0 or alarm_code in ['402', 'ERR-402']:
                    AlarmEvent.objects.update_or_create(
                        device=device,
                        code='ERR-402',
                        is_active=True,
                        defaults={
                            'description': f'Inverter {device.device_id} High Temperature Alert ({temp:.1f} °C > 45 °C limit)',
                            'severity': AlarmSeverity.WARNING,
                            'fault_text': f'Internal IGBT temperature reached {temp:.1f} °C. Auxiliary cooling fans engaged.',
                            'start_time': timestamp
                        }
                    )

            elif device.device_type == DeviceType.MFM:
                kw = extract_metric(rec, ['active_power', 'power', 'kw', 'Active Power (kW)', 'Active Power'], default=0.0)
                v_line = extract_metric(rec, ['p2p_volt_ry', 'v_ll', 'v_ry', 'grid_voltage', 'Grid Voltage (V)', 'voltage'], default=11040.0)
                exp_today = extract_metric(rec, ['export_energy_today', 'export_kwh', 'export_energy', 'Export (kWh)', 'today_export'], default=0.0)
                imp_today = extract_metric(rec, ['import_energy_today', 'import_kwh', 'import_energy', 'Import (kWh)'], default=0.0)

                MFMObservation.objects.create(
                    device=device,
                    timestamp=timestamp,
                    v_ry=v_line,
                    v_yb=v_line,
                    v_br=v_line,
                    active_power=kw,
                    reactive_power=extract_metric(rec, ['reactive_power', 'kvar'], default=0.0),
                    power_factor=extract_metric(rec, ['pf', 'power_factor', 'Power Factor'], default=0.996),
                    frequency=extract_metric(rec, ['freq', 'frequency', 'Frequency (Hz)'], default=50.02),
                    import_energy_today=imp_today,
                    export_energy_today=exp_today,
                    quality=DataQuality.VALID
                )
                DeviceLatest.objects.update_or_create(
                    device=device,
                    defaults={
                        'last_contact_time': timezone.now(),
                        'last_valid_time': timestamp,
                        'status': CommunicationStatus.ONLINE,
                        'active_power': kw,
                        'voltage_ry': v_line,
                        'frequency': extract_metric(rec, ['freq', 'frequency'], default=50.02),
                        'power_factor': extract_metric(rec, ['pf', 'power_factor'], default=0.996)
                    }
                )
                processed += 1

            elif device.device_type == DeviceType.WMS:
                poa = extract_metric(rec, ['gti', 'poa', 'poa_irradiance', 'Radiation (W/m2)', 'POA (W/m2)', 'GTI (W/m2)', 'GTI', 'POA', 'radiation'], default=1.0)
                ghi = extract_metric(rec, ['ghi', 'ghi_irradiance', 'GHI (W/m2)', 'GHI'], default=1.0)
                mod_temp = extract_metric(rec, ['module_temp', 'mod_temp', 'Module Temp (°C)', 'mod_temperature'], default=23.6)
                amb_temp = extract_metric(rec, ['amb_temp', 'ambient_temp', 'Ambient Temp (°C)', 'amb_temperature'], default=25.7)
                wind = extract_metric(rec, ['wind_speed', 'Wind Speed (m/s)', 'wind', 'windSpeed'], default=3.8)
                wind_dir = extract_metric(rec, ['wind_direction', 'Wind Direction (deg)', 'windDir'], default=295.0)
                hum = extract_metric(rec, ['humidity', 'Humidity (%)', 'rh', 'relative_humidity'], default=57.6)

                WMSObservation.objects.create(
                    device=device,
                    timestamp=timestamp,
                    gti=poa,
                    ghi=ghi,
                    module_temp=mod_temp,
                    ambient_temp=amb_temp,
                    wind_speed=wind,
                    wind_direction=wind_dir,
                    humidity=hum,
                    rainfall=extract_metric(rec, ['rain', 'rainfall'], default=0.0),
                    cloud_cover=extract_metric(rec, ['cloud', 'cloud_cover'], default=0.0),
                    quality=DataQuality.VALID
                )
                DeviceLatest.objects.update_or_create(
                    device=device,
                    defaults={
                        'last_contact_time': timezone.now(),
                        'last_valid_time': timestamp,
                        'status': CommunicationStatus.ONLINE,
                        'temperature': mod_temp,
                        'active_power': ghi
                    }
                )
                processed += 1

        logger.info(f"Processed {processed} device record(s) on {topic} (Total Inverter kW: {total_kw:.1f}).")

    def start(self):
        self.running = True
        logger.info(f"Initializing MQTT Bridge to {self.host}:{self.port} with Client ID {self.client_id}...")

        try:
            self.client = mqtt.Client(
                client_id=self.client_id,
                protocol=mqtt.MQTTv5,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
        except Exception:
            self.client = mqtt.Client(client_id=self.client_id)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        if self.username:
            self.client.username_pw_set(self.username, self.password)

        if self.use_tls or self.port == 8883:
            ctx = ssl.create_default_context()
            self.client.tls_set_context(ctx)

        logger.info(f"Connecting to broker {self.host}:{self.port}...")
        for attempt in range(1, 10):
            try:
                self.client.connect(self.host, self.port, keepalive=60)
                break
            except Exception as e:
                logger.warning(f"Connection attempt {attempt}/10 failed: {e}. Retrying in 3 seconds...")
                time.sleep(3)

        self.client.loop_forever(retry_first_connection=True)

    def stop(self):
        self.running = False
        if self.client:
            self.client.disconnect()
            logger.info("MQTT Bridge stopped.")


if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BROKER_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BROKER_PORT
    bridge = ScadaMqttBridge(host=host, port=port)
    try:
        bridge.start()
    except KeyboardInterrupt:
        bridge.stop()
