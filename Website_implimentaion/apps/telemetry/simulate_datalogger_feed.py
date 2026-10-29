#!/usr/bin/env python3
"""
Sunscrap / SATs Solar SCADA - Datalogger MQTT Simulation Script
Simulates the physical datalogger publishing authentic real-time solar telemetry
(all 13 inverters, 2 MFMs, and WMS meteorological station) to the EMQX broker.
Usage:
    python3 simulate_datalogger_feed.py --host <broker-host> --port 8883 --user vendor_logger_001 --password <password>
"""

import sys
import json
import time
import ssl
import argparse
from datetime import datetime
import paho.mqtt.client as mqtt

def build_telemetry_payload(sequence_num=1001):
    now_iso = datetime.now().astimezone().isoformat()

    records = []

    # 1. 13 Solar Inverters (INV-01 to INV-13)
    base_powers = [
        278.4, 279.1, 277.8, 281.2, 276.5, 280.0, 279.4,
        254.2, # INV-08 has thermal alert
        278.0, 281.8, 277.1, 279.8, 280.2
    ]

    for idx, base_kw in enumerate(base_powers, start=1):
        inv_id = f"INV-{idx:02d}"
        temp = 48.4 if idx == 8 else (43.8 + (idx % 3) * 0.5)
        status = "Warning" if idx == 8 else "Running"
        alarm = "ERR-402" if idx == 8 else "0"

        records.append({
            "device_id": inv_id,
            "timestamp": now_iso,
            "active_power": base_kw,
            "daily_yield": 915.2 + idx * 8.5,
            "vdc": 742.0 + (idx % 5),
            "idc": 412.0 + (idx % 3),
            "v_ry": 800.0,
            "v_yb": 800.0,
            "v_br": 800.0,
            "power_factor": 0.996,
            "frequency": 50.02,
            "temperature": temp,
            "operating_status": status,
            "alarm_code": alarm
        })

    # 2. 2 Multi-Function Meters (MFM-01 LT and MFM-02 Outgoing)
    records.append({
        "device_id": "MFM-01",
        "timestamp": now_iso,
        "active_power": 3248.5,
        "v_ry": 11042.0,
        "frequency": 50.02,
        "power_factor": 0.996,
        "export_kwh": 18450.6
    })
    records.append({
        "device_id": "MFM-02",
        "timestamp": now_iso,
        "active_power": 3245.0,
        "v_ry": 11040.0,
        "frequency": 50.02,
        "power_factor": 0.996,
        "export_kwh": 18430.0
    })

    # 3. Weather Monitoring Station (WMS-01)
    records.append({
        "device_id": "WMS-01",
        "timestamp": now_iso,
        "poa_irradiance": 892.0,
        "ghi_irradiance": 845.0,
        "module_temp": 48.2,
        "ambient_temp": 33.6,
        "wind_speed": 3.8,
        "wind_direction": 295.0,
        "humidity": 42.0
    })

    return {
        "collector_id": "sunscrap-logger-001",
        "sequence": sequence_num,
        "schema_version": "1.0",
        "timestamp": now_iso,
        "records": records
    }

def main():
    parser = argparse.ArgumentParser(description="Simulate Sunscrap Solar Datalogger MQTT Telemetry Feed")
    parser.add_argument("--host", required=True, help="MQTT Broker Hostname")
    parser.add_argument("--port", type=int, default=8883, help="MQTT Broker Port (default: 8883)")
    parser.add_argument("--user", default="vendor_logger_001", help="MQTT Username")
    parser.add_argument("--password", default="Telemetry#Gateway@9482", help="MQTT Password")
    parser.add_argument("--topic", default="scada/sunscrap/plant-01/logger-001/telemetry", help="MQTT Topic")
    parser.add_argument("--count", type=int, default=1, help="Number of test batches to publish (default: 1)")
    parser.add_argument("--no-tls", action="store_true", help="Disable TLS (for port 1883)")

    args = parser.parse_args()

    client_id = f"sunscrap-sim-logger-{int(time.time())}"
    print(f"Connecting to {args.host}:{args.port} as {args.user}...")

    try:
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    except Exception:
        client = mqtt.Client(client_id=client_id)

    client.username_pw_set(args.user, args.password)

    if not args.no_tls and args.port == 8883:
        ctx = ssl.create_default_context()
        client.tls_set_context(ctx)

    for attempt in range(1, 6):
        try:
            client.connect(args.host, args.port, keepalive=60)
            break
        except Exception as e:
            if attempt == 5:
                raise
            print(f"Connection attempt {attempt} failed: {e}. Retrying in 2s...")
            time.sleep(2)

    client.loop_start()

    for seq in range(1, args.count + 1):
        payload = build_telemetry_payload(sequence_num=seq)
        payload_json = json.dumps(payload, indent=2)

        info = client.publish(args.topic, payload_json, qos=1)
        info.wait_for_publish(timeout=5)

        print(f"[{seq}/{args.count}] Successfully published {len(payload['records'])} device records to {args.topic}")
        if seq < args.count:
            time.sleep(2)

    client.loop_stop()
    client.disconnect()
    print("Done! Test feed completed successfully.")

if __name__ == "__main__":
    main()
