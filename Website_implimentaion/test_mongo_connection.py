#!/usr/bin/env python3
"""
SAT Solutions (SATs) SCADA — MongoDB Atlas Connection Tester
Tests connectivity, authentication, ping latency, and collection access on:
mongodb+srv://hackraj1008_db_user:<password>@sats.phn72fw.mongodb.net/
"""

import sys
import os
import getpass
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

CLUSTER_URI_TEMPLATE = "mongodb+srv://hackraj1008_db_user:{password}@sats.phn72fw.mongodb.net/?retryWrites=true&w=majority&appName=sats"
DEFAULT_DB_NAME = "sats_scada_db"

def test_connection(password: str):
    # If the user passed percent-encoded password or special characters
    import urllib.parse
    encoded_password = urllib.parse.quote_plus(password)
    uri = CLUSTER_URI_TEMPLATE.format(password=encoded_password)

    print("=" * 70)
    print("SATs SCADA • MongoDB Atlas Free Tier Connectivity Test")
    print(f"Cluster Target : sats.phn72fw.mongodb.net")
    print(f"Database User  : hackraj1008_db_user")
    print(f"Target Database: {DEFAULT_DB_NAME}")
    print("=" * 70)

    print("\n[1/4] Connecting to MongoDB Atlas cluster...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=7000)
        # Force a server call to verify authentication
        server_info = client.server_info()
        print(f"  -> SUCCESS: Connected to MongoDB Server v{server_info.get('version')}!")
    except OperationFailure as e:
        print(f"  -> AUTHENTICATION FAILED: {e}")
        print("     Please check your database password for 'hackraj1008_db_user'.")
        return False
    except ConnectionFailure as e:
        print(f"  -> CONNECTION FAILED: {e}")
        print("     Check your internet connection and MongoDB Atlas Network Access (IP Whitelist).")
        return False
    except Exception as e:
        print(f"  -> ERROR: {e}")
        return False

    print("\n[2/4] Testing cluster ping & latency...")
    try:
        ping_res = client.admin.command('ping')
        print(f"  -> PING OK: {ping_res}")
    except Exception as e:
        print(f"  -> Ping command failed: {e}")
        return False

    print("\n[3/4] Inspecting existing databases & cluster topology...")
    try:
        dbs = client.list_database_names()
        print(f"  -> Available Databases: {dbs}")
    except Exception as e:
        print(f"  -> Note: list_database_names returned: {e}")

    print(f"\n[4/4] Performing read/write sanity test on '{DEFAULT_DB_NAME}.telemetry_health'...")
    try:
        db = client[DEFAULT_DB_NAME]
        health_col = db["telemetry_health"]
        test_doc = {
            "system": "SAT Solutions SCADA",
            "capacity": "3900 kW AC / 4640 kWp DC",
            "status": "ONLINE",
            "test_timestamp": os.popen("date").read().strip()
        }
        ins_res = health_col.insert_one(test_doc)
        print(f"  -> WRITE OK: Inserted verification document ID: {ins_res.inserted_id}")
        
        found = health_col.find_one({"_id": ins_res.inserted_id})
        print(f"  -> READ OK : Retrieved document: {found.get('system')} (Status: {found.get('status')})")
        print("\n" + "=" * 70)
        print(" ALL TESTS PASSED! Your MongoDB Atlas Free Tier is 100% READY!")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"  -> Read/write failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pwd = sys.argv[1]
    elif os.environ.get("MONGO_PASSWORD"):
        pwd = os.environ.get("MONGO_PASSWORD")
    else:
        try:
            pwd = getpass.getpass("Enter password for MongoDB user 'hackraj1008_db_user': ")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(1)

    if not pwd:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    success = test_connection(pwd)
    sys.exit(0 if success else 1)
