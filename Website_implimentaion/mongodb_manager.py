"""
SAT Solutions (SATs) SCADA — MongoDB Atlas Cloud Database Manager
Provides connection handling, real-time telemetry streaming, incident logging,
and plant profile synchronization with MongoDB Atlas Free Tier (M0 Sandbox).
"""

import os
import urllib.parse
from datetime import datetime, timezone
from pymongo import MongoClient

DEFAULT_CLUSTER_URI = os.environ.get(
    "MONGODB_URI",
    "mongodb+srv://hackraj1008_db_user:{password}@sats.phn72fw.mongodb.net/?retryWrites=true&w=majority&appName=sats"
)
DEFAULT_DB_NAME = os.environ.get("MONGODB_DB_NAME", "sats_scada_db")

class SATsMongoManager:
    _instance = None

    def __init__(self, uri=None, db_name=None):
        self.uri = uri or DEFAULT_CLUSTER_URI
        self.db_name = db_name or DEFAULT_DB_NAME
        self._client = None
        self._db = None

    @classmethod
    def get_instance(cls, uri=None, db_name=None):
        if cls._instance is None:
            cls._instance = cls(uri, db_name)
        return cls._instance

    def connect(self, password=None):
        """Establish connection with credentials."""
        if password and "{password}" in self.uri:
            encoded_pwd = urllib.parse.quote_plus(password)
            final_uri = self.uri.format(password=encoded_pwd)
        else:
            final_uri = self.uri

        self._client = MongoClient(final_uri, serverSelectionTimeoutMS=5000)
        self._db = self._client[self.db_name]
        return self._db

    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db

    def sync_telemetry_snapshot(self, inverters_list, plant_kpis):
        """Uploads a snapshot of real-time telemetry to MongoDB Atlas."""
        record = {
            "timestamp": datetime.now(timezone.utc),
            "plant_capacity": "3900 kW AC / 4640 kWp DC",
            "kpis": plant_kpis,
            "inverters_count": len(inverters_list),
            "inverters": inverters_list
        }
        return self.db["telemetry_snapshots"].insert_one(record)

    def log_alarm_incident(self, device, code, description, priority="CRITICAL"):
        """Logs an alarm event to the persistent incident audit collection."""
        alarm = {
            "timestamp": datetime.now(timezone.utc),
            "priority": priority,
            "device": device,
            "code": code,
            "description": description,
            "status": "ACTIVE_UNACKNOWLEDGED"
        }
        return self.db["alarm_incidents"].insert_one(alarm)

    def update_plant_specifications(self, profile_data):
        """Upserts the master plant profile in MongoDB."""
        return self.db["plant_profile"].update_one(
            {"facility_id": "SAT_SANAND_01"},
            {"$set": {**profile_data, "last_updated": datetime.now(timezone.utc)}},
            upsert=True
        )

    def get_recent_alarms(self, limit=20):
        """Fetches the latest alarms from MongoDB."""
        return list(self.db["alarm_incidents"].find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
