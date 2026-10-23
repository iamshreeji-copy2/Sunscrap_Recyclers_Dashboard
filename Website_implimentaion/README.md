# Sunscrap Solar SCADA — Telemetry & Analytics Platform

Independently built solar plant monitoring, operational reporting, and supervisory platform engineered for **Sunscrap Recyclers PVT LTD** (3,900 kW AC / 4,640 kWp DC).

---

## 🚀 Quick Start (Local Development)

### 1. Requirements
- Python 3.11+ (Python 3.13 tested)
- Pip dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Automatic Setup & Start
Run the bundled initialization and startup script:
```bash
./run_local.sh
```
Or execute manually:
```bash
python3 manage.py migrate
python3 manage.py seed_demo_data
python3 manage.py runserver 0.0.0.0:8000
```

### 3. Accessing the Application
- **URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Administrator Login:**
  - Username: `admin`
  - Password: `Sunscrap@2026`
- **Viewer / Operator Login:**
  - Username: `viewer`
  - Password: `Viewer@2026`
- **Captured Mailbox:**
  - Sent OTPs, password reset links, and report attachments are safely stored in `./data/captured_emails/`.

---

## 🧪 Automated Verification & Tests

To execute the test suite:
```bash
python3 manage.py test tests
```
**Test Coverage Includes:**
- Specific Yield (2.57 kWh/kWp) and 24h CUF (12.74%) calculation sanity
- Inverter efficiency calculation and PR evaluation
- Password authentication, session remember-me, and role authorization
- Six-digit OTP generation, attempt limiting (max 5), and expiry (5m)
- Password reset token generation and one-time invalidation
- All 23 required application routes tested for HTTP 200
- 6-Output Contract: CSV with formula defense, genuine XLSX with typed numbers & metadata sheet, and ReportLab PDF rendering
- Collector batch ingestion API (`/api/ingest/v1/batches`) with transactional idempotency

---

## 🖥️ Screen & Route Inventory

| Route | Functionality |
|---|---|
| `/login` | Password login with show/hide password and "remember me" |
| `/login/otp` | Request and verify 6-digit email OTP |
| `/forgot/password`, `/reset/password/<token>` | Password reset flow via captured mailbox |
| `/dashboard`, `/home` | Consolidated plant dashboard with dual-axis EChart & KPIs |
| `/inverters/overview` | Selector for 13 inverters, 12 MPPTs, 25 strings, and power charts |
| `/mfm/overview` | LT and Outgoing MFM selector, 3-phase snapshot, power/energy plots |
| `/reports/summary` | Daily generation summary across inverters, meter export, CUF, insolation |
| `/reports/energy/generation` | Substation export/import energy intervals and period totals |
| `/reports/inverter/generation` | Zone and inverter yield breakdown |
| `/reports/alarm` | Hardware alarm logs, severity badges, duration, acknowledgment |
| `/reports/trends` | 4 independently configurable trend panels with interactive ECharts |
| `/reports/custom-report` | Parameterized custom report builder with allowlisted metrics |
| `/reports/inverter/parameter` | Complete 69-column inverter history |
| `/reports/mfm/parameter` | Line/phase voltages, currents, powers, energy registers |
| `/reports/wms/parameter` | Ambient, module temperature, GHI, GTI, humidity, wind |
| `/reports/communication` | Device communication availability, SLA uptime, outage history |
| `/reports/downloads` | Download center with progress, checksum, expiring links |
| `/reports/schedules` | Automated daily, weekly, monthly report email schedules |
| `/settings/plant` | Plant name, organization, AC/DC ratings, timezone |
| `/settings/devices` | All 16 field devices, poll intervals, status |
| `/settings/system-health` | Disk headroom, database liveness, subsystem checks |
| `/settings/audit` | Append-only security and operational audit trail |

---

## 📥 Batch Ingestion API

To ingest telemetry batches from on-site edge gateways or Modbus pollers:
- **Endpoint:** `POST /api/ingest/v1/batches`
- **Content-Type:** `application/json`
- **Sample Request:**
```json
{
  "collector_id": "edge-gateway-substation",
  "sequence": 10452,
  "schema_version": "1.0",
  "records": [
    {
      "device_id": "INV-01",
      "timestamp": "2026-10-23T12:00:00+05:30",
      "active_power": 288.5,
      "daily_yield": 917.0,
      "dc_power": 293.2,
      "temperature": 48.5,
      "operating_status": "Running"
    }
  ]
}
```

---

## 🐳 Docker Production Deployment

To start with PostgreSQL, Redis, Celery, and Nginx reverse proxy:
```bash
cd docker
docker compose up -d --build
```
Web proxy is exposed on port `80`.
