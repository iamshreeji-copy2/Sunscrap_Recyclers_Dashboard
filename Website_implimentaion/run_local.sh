#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Starting Sunscrap Solar SCADA (Local Development Mode)"
echo " Organization: Sunscrap Recyclers PVT LTD"
echo " Plant: 3,900 kW AC / 4,640 kWp DC (Asia/Kolkata)"
echo "=========================================================="

python3 manage.py migrate --noinput
python3 manage.py seed_demo_data

PORT="${PORT:-8001}"

echo ""
echo "----------------------------------------------------------"
echo " Access Sunscrap Solar SCADA Application:"
echo " URL: http://127.0.0.1:$PORT"
echo " Administrator Account: username 'admin'   / password 'Sunscrap@2026'"
echo " Viewer Account:        username 'viewer'  / password 'Viewer@2026'"
echo " Captured Mailbox:      ./data/captured_emails/"
echo "----------------------------------------------------------"
echo "Launching local HTTP server on port $PORT..."

python3 manage.py runserver 0.0.0.0:$PORT
