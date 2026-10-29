#!/usr/bin/env python3
"""
Sunscrap / SATs Solar SCADA - Datalogger MQTT Simulation Script
Simulates the physical datalogger publishing authentic real-time solar telemetry
across the developer topics (sunscrap/data/INV_1 .. INV_13, sunscrap/data/WMS, sunscrap/data/MFM)
with individual string current tables ("String #", "Current (A)", "Status").
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

def generate_string_table(inv_num, base_current=8.4):
    strings = []
    for s_idx in range(1, 26):
        # Inverter 08 has slight current drop on String 14, and Inverter 03 String 14 warning
        if inv_num == 8 and s_idx == 14:
            c = round(base_current * 0.72, 2)
            stat = "Warning"
        elif inv_num == 3 and s_idx == 14:
            c = round(base_current * 0.35, 2)
            stat = "Warning"
        else:
            jitter = ((s_idx * 7 + inv_num * 13) % 19 - 9) * 0.02
            c = round(base_current + jitter, 2)
            stat = "Normal"
        strings.append({
            "String #": s_idx,
            "Current (A)": c,
            "Status": stat
        })
    return strings

def main():
    parser = argparse.ArgumentParser(description="Simulate Sunscrap Solar Datalogger MQTT Telemetry Feed")
    parser.add_argument("--host", default="k6fc1317.ala.dedicated.aws.emqxcloud.com", help="MQTT Broker Hostname")
    parser.add_argument("--port", type=int, default=8883, help="MQTT Broker Port (default: 8883)")
    parser.add_argument("--user", default="vendor_logger_001", help="MQTT Username")
    parser.add_argument("--password", default="Telemetry#Gateway@9482", help="MQTT Password")
    parser.add_argument("--topic-prefix", default="sunscrap/data", help="Topic base prefix (default: sunscrap/data)")
    parser.add_argument("--count", type=int, default=1, help="Number of test rounds to publish (default: 1)")
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

    base_powers = [
        278.4, 279.1, 277.8, 281.2, 276.5, 280.0, 279.4,
        254.2,  # INV-08 has thermal alert
        278.0, 281.8, 277.1, 279.8, 280.2
    ]

    for round_idx in range(1, args.count + 1):
        now_iso = datetime.now().astimezone().isoformat()
        print(f"\n--- Publishing Round {round_idx}/{args.count} [{now_iso}] ---")

        # 1. Publish 13 Inverters to sunscrap/data/INV_1 .. sunscrap/data/INV_13
        for idx, base_kw in enumerate(base_powers, start=1):
            inv_topic = f"{args.topic_prefix}/INV_{idx}"
            temp = 48.4 if idx == 8 else (43.8 + (idx % 3) * 0.5)
            status = "Warning" if idx in [3, 8] else "Running"
            alarm = "ERR-402" if idx == 8 else ("W021" if idx == 3 else "0")
            strings = generate_string_table(idx)

            payload = {
                "device_id": f"INV-{idx:02d}",
                "timestamp": now_iso,
                "active_power": base_kw,
                "daily_yield": 920.0 + idx * 8.5,
                "vdc": 745.0 + (idx % 5),
                "idc": round(sum(s["Current (A)"] for s in strings), 1),
                "v_ry": 800.0,
                "power_factor": 0.996,
                "frequency": 50.02,
                "temperature": temp,
                "operating_status": status,
                "alarm_code": alarm,
                "strings": strings
            }

            inf = client.publish(inv_topic, json.dumps(payload), qos=1)
            inf.wait_for_publish(timeout=3)
            print(f"  ✓ Published {inv_topic} ({base_kw} kW, {len(strings)} strings)")

        # 2. Publish WMS to sunscrap/data/WMS
        wms_topic = f"{args.topic_prefix}/WMS"
        wms_payload = {
            "device_id": "WMS-01",
            "timestamp": now_iso,
            "poa_irradiance": 895.0,
            "ghi_irradiance": 848.0,
            "module_temp": 48.5,
            "ambient_temp": 33.8,
            "wind_speed": 3.9,
            "wind_direction": 290.0,
            "humidity": 41.5
        }
        inf = client.publish(wms_topic, json.dumps(wms_payload), qos=1)
        inf.wait_for_publish(timeout=3)
        print(f"  ✓ Published {wms_topic} (POA: 895 W/m²)")

        # 3. Publish MFM to sunscrap/data/MFM
        mfm_topic = f"{args.topic_prefix}/MFM"
        mfm_payload = {
            "device_id": "MFM-LT",
            "timestamp": now_iso,
            "active_power": 3252.0,
            "v_ll": 11045.0,
            "frequency": 50.02,
            "power_factor": 0.996,
            "export_kwh": 18510.0
        }
        inf = client.publish(mfm_topic, json.dumps(mfm_payload), qos=1)
        inf.wait_for_publish(timeout=3)
        print(f"  ✓ Published {mfm_topic} (Export: 3252 kW)")

        if round_idx < args.count:
            time.sleep(2)

    client.loop_stop()
    client.disconnect()
    print("\nAll developer topics published successfully!")

if __name__ == "__main__":
    main()
