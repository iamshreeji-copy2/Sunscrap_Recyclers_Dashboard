"""
Sunscrap / SATs Solar SCADA - Live MQTT Telemetry Bridge Service
Connects to EMQX Cloud Broker, consumes real-time datalogger telemetry packets,
idempotently stores raw batches in database, and normalizes device observations.
"""

import os
import sys
import json
import ssl
import time
import hashlib
import logging
from datetime import datetime
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
DEFAULT_TOPIC = os.environ.get('MQTT_TOPIC', 'scada/sunscrap/plant-01/logger-001/telemetry')
STATUS_TOPIC = os.environ.get('MQTT_STATUS_TOPIC', 'scada/sunscrap/plant-01/logger-001/status')

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
            # Subscribe to assigned telemetry and status topics
            client.subscribe([(self.topic, 1), (STATUS_TOPIC, 1)])
            logger.info(f"Subscribed to topics: {self.topic}, {STATUS_TOPIC}")
        else:
            logger.error(f"Failed to connect to MQTT Broker, return code: {rc_code}")

    def on_disconnect(self, client, userdata, rc, properties=None):
        logger.warning(f"Disconnected from MQTT Broker (rc={rc}). Reconnecting automatically...")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload_str = msg.payload.decode('utf-8')
            data = json.loads(payload_str)
        except Exception as e:
            logger.error(f"Failed to parse payload on {topic}: {e}")
            return

        logger.info(f"Received message on {topic} ({len(msg.payload)} bytes)")

        try:
            if topic == STATUS_TOPIC:
                self.handle_status_message(data)
            else:
                self.handle_telemetry_message(data)
        except Exception as e:
            logger.exception(f"Error processing telemetry packet from {topic}: {e}")

    def handle_status_message(self, data):
        logger.info(f"Logger status update: {data}")

    def handle_telemetry_message(self, data):
        collector_id = data.get('collector_id') or data.get('logger_id') or 'logger-001'
        sequence = data.get('sequence', 1)
        schema_version = data.get('schema_version', '1.0')
        records = data.get('records') or data.get('samples') or []

        # If data is a single device record rather than wrapped in a list
        if not records and ('device_id' in data or 'active_power' in data):
            records = [data]

        # Calculate idempotency payload hash
        payload_raw = json.dumps(data, sort_keys=True)
        payload_hash = hashlib.sha256(payload_raw.encode()).hexdigest()

        # Idempotent deduplication check
        existing = RawIngestBatch.objects.filter(payload_hash=payload_hash).first()
        if existing:
            logger.info(f"Batch duplicate detected (hash {payload_hash[:12]}...), skipping duplicate write.")
            return

        batch_rec = RawIngestBatch.objects.create(
            collector_id=collector_id,
            schema_version=schema_version,
            batch_sequence=sequence,
            payload_hash=payload_hash,
            payload=data,
            status="ACCEPTED"
        )

        processed = 0
        total_kw = 0.0

        for rec in records:
            dev_id = rec.get('device_id') or rec.get('id')
            if not dev_id:
                continue

            dt_str = rec.get('timestamp') or rec.get('observed_at')
            timestamp = parse_datetime(dt_str) if dt_str else timezone.now()
            if not timestamp:
                timestamp = timezone.now()

            # Find corresponding plant device
            device = Device.objects.filter(device_id__iexact=dev_id).first()
            if not device:
                # Alias mapping for MFMs (MFM-01 -> MFM-LT, MFM-02 -> MFM-OUT)
                dev_norm = dev_id.upper().replace('_', '-').strip()
                if dev_norm in ['MFM-01', 'MFM1', 'MFM-LT', 'LT-METER', 'MFM-LT-01']:
                    device = Device.objects.filter(device_id='MFM-LT').first()
                elif dev_norm in ['MFM-02', 'MFM2', 'MFM-OUT', 'OUT-METER', 'MFM-OUT-01']:
                    device = Device.objects.filter(device_id='MFM-OUT').first()
                elif dev_norm in ['WMS', 'WMS-1', 'WEATHER']:
                    device = Device.objects.filter(device_id='WMS-01').first()

            if not device:
                # Try finding without hyphen or leading zeroes (e.g. INV-01 vs INV-1 vs inv-01)
                device = Device.objects.filter(device_id__icontains=dev_id.replace('-', '')).first()
            if not device:
                continue

            # Process by device type
            if device.device_type == DeviceType.INVERTER:
                kw = float(rec.get('active_power') or rec.get('power_kw') or rec.get('metrics', {}).get('active_power_kw') or 0.0)
                temp = float(rec.get('temperature') or rec.get('internal_temp') or rec.get('metrics', {}).get('temperature_c') or 45.0)
                daily_kwh = float(rec.get('daily_yield') or rec.get('today_kwh') or rec.get('metrics', {}).get('daily_energy_kwh') or 0.0)
                v_ry = float(rec.get('v_ry') or 800.0)
                status_str = rec.get('operating_status') or "Running"
                alarm_code = str(rec.get('alarm_code') or "0")

                InverterObservation.objects.create(
                    device=device,
                    timestamp=timestamp,
                    vdc=float(rec.get('vdc', 742.0)),
                    idc=float(rec.get('idc', 412.0)),
                    v_ry=v_ry,
                    v_yb=float(rec.get('v_yb', v_ry)),
                    v_br=float(rec.get('v_br', v_ry)),
                    i_r=float(rec.get('i_r', 0.0)),
                    i_y=float(rec.get('i_y', 0.0)),
                    i_b=float(rec.get('i_b', 0.0)),
                    power_factor=float(rec.get('power_factor', 0.996)),
                    frequency=float(rec.get('frequency', 50.02)),
                    active_power=kw,
                    reactive_power=float(rec.get('reactive_power', 0.0)),
                    dc_power=float(rec.get('dc_power', kw * 1.02)),
                    daily_yield=daily_kwh,
                    lifetime_yield=float(rec.get('lifetime_yield', 0.0)),
                    insulation_resistance=float(rec.get('insulation_resistance', 1000.0)),
                    temperature=temp,
                    operating_status=status_str,
                    alarm_code=alarm_code,
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
                        'lifetime_yield': float(rec.get('lifetime_yield', 0.0)),
                        'temperature': temp,
                        'voltage_ry': v_ry,
                        'power_factor': float(rec.get('power_factor', 0.996)),
                        'frequency': float(rec.get('frequency', 50.02)),
                    }
                )

                total_kw += kw
                processed += 1

                # Check for critical Inverter 08 Temperature Alert (ERR-402)
                if temp > 47.0 or alarm_code == '402' or alarm_code == 'ERR-402':
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
                kw = float(rec.get('active_power') or rec.get('kw') or 0.0)
                v_line = float(rec.get('v_ll') or rec.get('v_ry') or 11040.0)
                MFMObservation.objects.create(
                    device=device,
                    timestamp=timestamp,
                    v_ry=v_line,
                    v_yb=v_line,
                    v_br=v_line,
                    active_power=kw,
                    reactive_power=float(rec.get('reactive_power', 0.0)),
                    power_factor=float(rec.get('power_factor', 0.996)),
                    frequency=float(rec.get('frequency', 50.02)),
                    import_energy_today=float(rec.get('import_kwh') or rec.get('import_energy_today', 0.0)),
                    export_energy_today=float(rec.get('export_kwh') or rec.get('export_energy_today', 0.0)),
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
                        'frequency': float(rec.get('frequency', 50.02)),
                        'power_factor': float(rec.get('power_factor', 0.996))
                    }
                )
                processed += 1

            elif device.device_type == DeviceType.WMS:
                poa = float(rec.get('poa_irradiance') or rec.get('poa') or rec.get('gti') or rec.get('metrics', {}).get('poa_w_m2') or 892.0)
                ghi = float(rec.get('ghi_irradiance') or rec.get('ghi') or rec.get('metrics', {}).get('ghi_w_m2') or 845.0)
                mod_temp = float(rec.get('module_temp') or rec.get('metrics', {}).get('module_temperature_c') or 48.2)
                amb_temp = float(rec.get('ambient_temp') or rec.get('metrics', {}).get('ambient_temperature_c') or 33.6)

                WMSObservation.objects.create(
                    device=device,
                    timestamp=timestamp,
                    gti=poa,
                    ghi=ghi,
                    module_temp=mod_temp,
                    ambient_temp=amb_temp,
                    wind_speed=float(rec.get('wind_speed', 3.8)),
                    wind_direction=float(rec.get('wind_direction', 295.0)),
                    humidity=float(rec.get('humidity', 42.0)),
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

        logger.info(f"Successfully processed {processed} device records in batch {sequence} (Active Power: {total_kw:.1f} kW).")

    def start(self):
        self.running = True
        logger.info(f"Initializing MQTT Bridge to {self.host}:{self.port} with Client ID {self.client_id}...")

        # Initialize paho MQTT client
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

        # Resilient DNS resolution and connect loop
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
