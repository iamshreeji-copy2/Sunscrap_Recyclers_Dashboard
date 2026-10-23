# Sunscrap Solar SCADA — Telemetry & Analytics Platform

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen?style=for-the-badge&logo=github)](https://iamshreeji-copy2.github.io/iamshreeji-copy2/)
[![Plant Rating](https://img.shields.io/badge/AC%20Capacity-3%2C900%20kW-blue?style=for-the-badge)](https://iamshreeji-copy2.github.io/iamshreeji-copy2/)
[![Plant Rating](https://img.shields.io/badge/DC%20Capacity-4%2C640%20kWp-orange?style=for-the-badge)](https://iamshreeji-copy2.github.io/iamshreeji-copy2/)
[![Tests](https://img.shields.io/badge/Automated%20Tests-100%25%20Passing-success?style=for-the-badge)](https://iamshreeji-copy2.github.io/iamshreeji-copy2/)

> **Live Interactive GitHub Pages Demo:**  
> 👉 **[https://iamshreeji-copy2.github.io/iamshreeji-copy2/](https://iamshreeji-copy2.github.io/iamshreeji-copy2/)**

Independently built solar plant monitoring, operational reporting, and supervisory platform engineered for **Sunscrap Recyclers PVT LTD** (3,900 kW AC / 4,640 kWp DC, Asia/Kolkata).

---

## ✨ Key New Features Implemented

### 1. ♿ Accessibility Hub (Colors, Font Scaling, Light & Dark Mode)
A dedicated, prominent **Accessibility** trigger button in the top header and persistent floating hub:
- **Display Modes (Light / Dark):**
  - **☀️ Light Mode:** Clean high-clarity day mode.
  - **🌙 Dark Mode:** Sleek deep-navy control-room dark theme (`#0B132B` / `#17223B`) designed for low-light night shifts.
- **Color Vision Themes:**
  - 🌈 **Vibrant Sunscrap Theme:** Modern solar blue, bright gold, and clean status indicators.
  - ⚪ **Monochrome Grayscale Mode:** High-contrast grayscale mode for accessible and low-fatigue operations.
  - 🔲 **High-Contrast Outdoor Mode:** Maximized element contrast for outdoor tablet visibility.
- **Typography Font Scaling:**
  - One-click presets: `85%`, `100%`, `115%`, `125%`.
  - Incremental stepping controls: `A−` (decrease), `Reset`, `A+` (increase).
- **Reduced Motion:** Low-latency mode disabling heavy CSS animations.
- *All settings are instantly persisted to `localStorage`.*

---

### 2. 💰 Commercial Revenue & Electricity Yield Engine (INR ₹ & Multi-Currency)
Real-time financial yield calculator on the Plant Dashboard that dynamically translates solar kilowatt-hours into monetary commercial revenue:
$$\text{Revenue} = \text{Energy Units Produced (kWh)} \times \text{Tariff Rate per Unit}$$

- **Multi-Currency Support:**
  - **INR (₹) — Indian Rupee** (Default: `₹3.00 / unit`)
  - **USD ($) — US Dollar** (Default: `$0.035 / unit`)
  - **EUR (€) — Euro** (Default: `€0.033 / unit`)
  - **GBP (£) — British Pound** (Default: `£0.028 / unit`)
- **Interactive Tariff Presets & Inputs:**
  - Instant preset buttons (`₹2.50`, `₹3.00`, `₹3.50`, `₹4.20`) and custom decimal rate input.
- **Commercial Outputs Computed:**
  - **Today's Inverter Revenue:** `11,921.30 kWh × ₹3.00 = ₹ 35,763.90`
  - **Grid Substation Export Revenue:** `11,778.24 kWh × ₹3.00 = ₹ 35,334.72`
  - **Lifetime Plant Commercial Value:** `1,567,546 kWh × ₹3.00 = ₹ 47,02,638.00`
  - Uses localized Indian numbering notation (`₹ 47,02,638.00` / 47.02 Lakhs).

---

## 🖥️ Screen & Route Inventory (All 23 Functional Screens)

| Screen / Feature | Route | Live Demo Path |
|---|---|---|
| **Consolidated Plant Dashboard** | `/dashboard`, `/home` | [`index.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/index.html) |
| **Inverter Overview (13 Inverters)** | `/inverters/overview` | [`inverter_overview.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/inverter_overview.html) |
| **MFM Overview (LT & Outgoing)** | `/mfm/overview` | [`mfm_overview.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/mfm_overview.html) |
| **Plant Generation Summary** | `/reports/summary` | [`report_summary.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_summary.html) |
| **Energy Generation (Export/Import)** | `/reports/energy/generation` | [`report_energy_generation.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_energy_generation.html) |
| **Inverter Generation Yield** | `/reports/inverter/generation` | [`report_inverter_generation.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_inverter_generation.html) |
| **Hardware Alarms & Faults Lifecycle** | `/reports/alarm` | [`report_alarm.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_alarm.html) |
| **Interactive Multi-Trends (4-Panel)** | `/reports/trends` | [`report_trends.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_trends.html) |
| **Custom Parameterized Report Builder** | `/reports/custom-report` | [`report_custom.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_custom.html) |
| **Inverter Full 69 Parameters** | `/reports/inverter/parameter` | [`report_inverter_parameter.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_inverter_parameter.html) |
| **MFM Electrical Parameters** | `/reports/mfm/parameter` | [`report_mfm_parameter.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_mfm_parameter.html) |
| **Weather & Environmental Parameters** | `/reports/wms/parameter` | [`report_wms_parameter.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_wms_parameter.html) |
| **Communication Health & SLA Uptime** | `/reports/communication` | [`report_communication.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/report_communication.html) |
| **Downloads Center** | `/reports/downloads` | [`downloads.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/downloads.html) |
| **Automated Report Schedules** | `/reports/schedules` | [`schedules.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/schedules.html) |
| **Operator Sign In** | `/login` | [`login.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/login.html) |
| **Operator Profile & Security** | `/profile` | [`profile.html`](https://iamshreeji-copy2.github.io/iamshreeji-copy2/profile.html) |

---

## 📋 The Complete 6-Output Contract
Every report and data table is equipped with:
1. **Copy:** Sanitized tab-separated clipboard format.
2. **Excel:** Genuine `.xlsx` with numeric typed cells and metadata audit sheet.
3. **CSV:** UTF-8 RFC 4180 CSV with formula injection mitigation (escaping leading `=`, `+`, `-`, `@`).
4. **PDF:** Server-rendered landscape PDF with clean margins, headings, and pagination.
5. **Print:** Authenticated dedicated printable view.
6. **Email:** Modal dialog allowing direct email dispatch of generated report snapshot.

---

## 🚀 Running the Django Full-Stack Application Locally

```bash
cd Website_implimentaion
./run_local.sh
```

- **Local URL:** `http://127.0.0.1:8001` (or port 8000)
- **Administrator Login:** `admin` / `Sunscrap@2026`
- **Viewer / Operator Login:** `viewer` / `Viewer@2026`
- **Captured Mailbox:** `./data/captured_emails/`

### Running Automated Test Suite
```bash
cd Website_implimentaion
python3 manage.py test tests
```
*7/7 comprehensive automated test suites pass with 100% OK in ~4.3 seconds.*

---

## 🐳 Docker Production Setup

```bash
cd Website_implimentaion/docker
docker compose up -d --build
```
Includes PostgreSQL 16, Redis 7, Django Gunicorn WSGI workers, and Nginx reverse proxy.
