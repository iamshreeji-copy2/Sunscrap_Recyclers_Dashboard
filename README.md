# Sunscrap Solar SCADA — Telemetry & Analytics Platform

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen?style=for-the-badge&logo=github)](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/)
[![Plant Rating](https://img.shields.io/badge/AC%20Capacity-3%2C900%20kW-blue?style=for-the-badge)](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/)
[![Plant Rating](https://img.shields.io/badge/DC%20Capacity-4%2C640%20kWp-orange?style=for-the-badge)](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/)
[![Tests](https://img.shields.io/badge/Automated%20Tests-100%25%20Passing-success?style=for-the-badge)](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/)

> **Live Interactive GitHub Pages Demo:**  
> 👉 **[https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/)**
> 
> **GitHub Repository:**  
> 👉 **[https://github.com/iamshreeji-copy2/Sunscrap_Recyclers_Dashboard](https://github.com/iamshreeji-copy2/Sunscrap_Recyclers_Dashboard)**

Independently built solar plant monitoring, operational reporting, and supervisory platform engineered for **Sunscrap Recyclers PVT LTD** (3,900 kW AC / 4,640 kWp DC, Asia/Kolkata).

---

## ✨ Key Capabilities & Latest Features

### 1. 🚨 Critical Alarm Siren & Blinking Red Screen Pop-up System
An industrial-grade supervisory alarm and alert dispatch system:
- **Audio Siren Engine:** Synthesizes an alternating dual-tone emergency acoustic siren (880 Hz / 620 Hz alternating tone) using the browser's native **HTML5 Web Audio API** (`AudioContext`). Works 100% offline with zero dependencies on external audio files.
- **Blinking Red Screen Strobe:** When an alarm triggers, the entire screen pulses with an animated high-visibility red vignette overlay (`@keyframes alertStrobeAnim`) and glowing modal border.
- **Emergency Action Buttons:**
  - **Cancel & Silence Siren:** Instantly terminates the acoustic oscillator, dismisses the red strobe, and silences the warning.
  - **Go to Alert Logs:** Silences the siren and immediately redirects the operator directly to the Alert Logs page (`report_alarm.html#alert-logs`), scrolling straight to the active log entry.
- **Alert Center & Thresholds:** Configure trip thresholds for Inverter Active Power Drop, Module High Temperature (> 65°C), Communication Outages, and Grid Under-Voltage. Includes a **⚡ Test Live Alert** simulation button.
- **Persistent Alert Logs:** Automatically timestamps and logs each alarm event to local storage and the database table.

---

### 2. 📱 Instant WhatsApp Sharing & Email Dispatch
Integrated into every report and data table toolbar:
- **Share on WhatsApp:** One-click WhatsApp button formatted with WhatsApp brand green (`#25D366`). Formats and encodes plant operational summary:
  - Organization Name, Plant Rating (3,900 kW AC / 4,640 kWp DC)
  - Report Title and Date
  - Operational Inverters (13/13 Online)
  - Generation and Grid Export Metrics
  - Direct live URL to the SCADA portal
- **Email Report:** Modal dialog enabling automated email dispatch of report snapshots in genuine XLSX, CSV, or PDF formats to operational mailing lists.

---

### 3. 📦 Multi-Format ZIP Archive Downloader
- **Download as ZIP:** Bundles report data into a genuine `.zip` archive on demand.
- Contains:
  - High-precision UTF-8 CSV with formula injection defense
  - Tab-delimited TSV data
  - Audit trail text file with organization metadata, date, timezone, and device counts
  - Historical Excel report sheets
- Implemented with both a Django backend generator (`/reports/export/zip`) and a pure, zero-dependency client-side PKZIP binary writer for instant browser downloads on GitHub Pages.

---

### 4. 📅 Daily & Monthly Historical Reports
Directly integrates historical production data from `/Reports`:
- **Mode Switcher:** Toggle between **Daily** mode (viewing specific dates from `2026-10-18` to `2026-10-23`) and **Monthly** mode (viewing all days of the month for `2026-10`, `2026-09`, `2026-08`, `2026-07`, `2026-06`, `2026-05`).
- Exact column alignment:
  `Date` | `Inverters 1 to 13 Generation (kWh)` | `TOTAL Inverter Generation (kWh)` | `Day Export (kWh)` | `Day Import (kWh)` | `NET Generation (kWh)` | `Generation Guarantee` | `CUF Plant End (%)` | `CUF GETCO End (%)` | `GHI Energy (kWh/m²/day)` | `GHI Average (W/m²)` | `Ambient Temp (°C)` | `Module Temp (°C)`
- Original Excel workbooks vendored in `static/data/reports/` for direct download.

---

### 5. ⇅ Universal Interactive Table Column Sorting
- Every table header (`<th>`) is interactive with sort indicators (`⇅`, `▲`, `▼`).
- Click once for **Ascending**, click again for **Descending**.
- Automatically detects and handles numeric units (`kWh`, `kW`, `°C`, `W/m²`, `₹`, `%`), timestamps, and strings.

---

### 6. ♿ Accessibility Hub (Colors, Font Scaling, Light & Dark Mode)
- **Display Modes:** ☀️ Light Mode & 🌙 Deep Navy Control-Room Dark Theme (`#0B132B` / `#17223B`).
- **Color Themes:** 🌈 Vibrant Sunscrap, ⚪ Monochrome Grayscale, 🔲 High-Contrast Outdoor Tablet Mode.
- **Typography Scaling:** `85%`, `100%`, `115%`, `125%` presets + `A-` / `A+` stepping.
- **Preferences:** Persisted locally in browser `localStorage`.

---

### 7. 💰 Commercial Revenue & Electricity Yield Engine
Real-time financial yield calculator on the Plant Dashboard:
$$\text{Revenue} = \text{Energy Units Produced (kWh)} \times \text{Tariff Rate per Unit}$$
- **Currencies:** INR (₹), USD ($), EUR (€), GBP (£)
- **Interactive Presets:** `₹2.50`, `₹3.00`, `₹3.50`, `₹4.20` + custom input
- **Computed Outputs:**
  - Today's Inverter Revenue: `11,921.30 kWh × ₹3.00 = ₹ 35,763.90`
  - Substation Export Revenue: `11,778.24 kWh × ₹3.00 = ₹ 35,334.72`
  - Lifetime Commercial Value: `1,567,546 kWh × ₹3.00 = ₹ 47,02,638.00` (47.02 Lakhs)

---

## 🖥️ Screen & Route Inventory

| Screen / Feature | Route | Live Demo Path |
|---|---|---|
| **Consolidated Plant Dashboard** | `/dashboard`, `/home` | [`index.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/index.html) |
| **Inverter Overview (13 Inverters)** | `/inverters/overview` | [`inverter_overview.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/inverter_overview.html) |
| **MFM Overview (LT & Outgoing)** | `/mfm/overview` | [`mfm_overview.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/mfm_overview.html) |
| **Plant Generation Summary** | `/reports/summary` | [`report_summary.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_summary.html) |
| **Energy Generation (Export/Import)** | `/reports/energy/generation` | [`report_energy_generation.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_energy_generation.html) |
| **Inverter Generation Yield** | `/reports/inverter/generation` | [`report_inverter_generation.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_inverter_generation.html) |
| **Hardware Alarms & Faults Lifecycle** | `/reports/alarm` | [`report_alarm.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_alarm.html) |
| **Interactive Multi-Trends (4-Panel)** | `/reports/trends` | [`report_trends.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_trends.html) |
| **Custom Parameterized Report Builder** | `/reports/custom-report` | [`report_custom.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_custom.html) |
| **Inverter Full 69 Parameters** | `/reports/inverter/parameter` | [`report_inverter_parameter.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_inverter_parameter.html) |
| **MFM Electrical Parameters** | `/reports/mfm/parameter` | [`report_mfm_parameter.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_mfm_parameter.html) |
| **Weather & Environmental Parameters** | `/reports/wms/parameter` | [`report_wms_parameter.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_wms_parameter.html) |
| **Communication Health & SLA Uptime** | `/reports/communication` | [`report_communication.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/report_communication.html) |
| **Downloads Center** | `/reports/downloads` | [`downloads.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/downloads.html) |
| **Automated Report Schedules** | `/reports/schedules` | [`schedules.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/schedules.html) |
| **Operator Sign In & OTP Simulation** | `/login` | [`login.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/login.html) |
| **Operator Profile & Security** | `/profile` | [`profile.html`](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/profile.html) |

---

## 📋 The Complete 8-Output Contract
Every report and data table is equipped with:
1. **Copy:** Sanitized tab-separated clipboard format.
2. **Excel:** Genuine `.xlsx` with numeric typed cells and metadata audit sheet.
3. **CSV:** UTF-8 RFC 4180 CSV with formula injection mitigation (escaping leading `=`, `+`, `-`, `@`).
4. **PDF:** Server-rendered landscape PDF with clean margins, headings, and pagination.
5. **Print:** Authenticated dedicated printable view.
6. **Email:** Modal dialog allowing direct email dispatch of generated report snapshot.
7. **WhatsApp:** Formatted plant metrics dispatched directly to WhatsApp.
8. **ZIP:** Bundled archive package with CSV, TSV, metadata, and original workbooks.

---

## 🚀 Running Locally

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
