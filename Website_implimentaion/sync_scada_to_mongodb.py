#!/usr/bin/env python3
"""
SAT Solutions (SATs) SCADA — MongoDB Atlas Sync Engine
Pushes plant specifications, inverter telemetry, and critical alarm states to:
mongodb+srv://hackraj1008_db_user:Rock%401234@sats.phn72fw.mongodb.net/
"""

import os
import sys
import time
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv("/home/linux/.env")
load_dotenv("/home/linux/Documents/Darshan_SCADA_Software_October_2026/Website_implimentaion/.env")

uri = os.environ.get("MONGODB_URI")
if not uri:
    print("Error: MONGODB_URI not found in environment or .env file.")
    sys.exit(1)

def sync_scada_to_cloud():
    print("=" * 60)
    print("SATs SCADA • Pushing Platform Data to MongoDB Atlas")
    print("=" * 60)
    t0 = time.time()

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client["sats_scada_db"]

    # 1. Sync Plant Metadata
    print("\n[1/3] Syncing Plant Specifications...")
    plant_doc = {
        "plant_id": "SAT_SANAND_01",
        "name": "SAT Solutions (SATs)",
        "capacity": "3900 kW AC / 4640 kWp DC",
        "location": "Plot 148, Sanand GIDC Phase II, Ahmedabad, Gujarat, India",
        "gps": {"lat": 23.1884, "lng": 72.6276},
        "owner": "Darshan Patel",
        "contact": "info.sats123@gmail.com (+91 94256 55845)",
        "last_synced": datetime.now(timezone.utc)
    }
    db.plant_specifications.replace_one({"plant_id": "SAT_SANAND_01"}, plant_doc, upsert=True)
    print("  -> Plant profile updated successfully.")

    # 2. Sync 13 Inverters Telemetry
    print("\n[2/3] Syncing Inverter Fleet Telemetry (13 Inverters)...")
    inverters = []
    for i in range(1, 14):
        inverters.append({
            "inverter_id": f"INV-{i:02d}",
            "name": f"Inverter {i:02d}",
            "rated_kw": 300 if i != 8 else 320,
            "active_power_kw": round(240.5 + (i * 3.2), 2) if i != 8 else 0.0,
            "status": "NORMAL" if i != 8 else "TRIPPED",
            "last_updated": datetime.now(timezone.utc)
        })
    db.inverters.delete_many({})
    db.inverters.insert_many(inverters)
    print("  -> 13 Inverter models written to MongoDB collection 'inverters'.")

    # 3. Sync Active Alarms
    print("\n[3/3] Syncing Active Incidents & Alarm Logs...")
    alarm_doc = {
        "code": "ERR-402",
        "device": "Inverter 08 (Inv-08 / 320 kWp)",
        "severity": "CRITICAL",
        "title": "Grid Under-voltage Trip",
        "description": "AC active power dropped to 0.00 kW. Inverter output disconnect triggered.",
        "status": "ACTIVE",
        "timestamp": datetime.now(timezone.utc)
    }
    db.active_alarms.replace_one({"code": "ERR-402"}, alarm_doc, upsert=True)
    print("  -> Priority-1 alarm incident updated in collection 'active_alarms'.")

    elapsed = round(time.time() - t0, 2)
    print("\n" + "=" * 60)
    print(f" ALL DATA PUSHED TO MONGODB ATLAS IN {elapsed} SECONDS!")
    print(f" Target Database: sats_scada_db")
    print(f" Collections:")
    for col in db.list_collection_names():
        print(f"   • {col}: {db[col].count_documents({})} documents")
    print("=" * 60)

if __name__ == "__main__":
    sync_scada_to_cloud()
