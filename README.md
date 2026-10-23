# Sunscrap Solar SCADA v2.4 — Sunscrap Recyclers PVT LTD

A production-grade Solar Photovoltaic SCADA & Intelligent Analytics Platform engineered for **Sunscrap Recyclers PVT LTD** (3,900 kW AC / 4,640 kWp DC Grid-Tied Solar Power Facility located in Sanand GIDC Phase II, Ahmedabad, Gujarat, India).

[![GitHub Pages Deployment](https://img.shields.io/badge/GitHub%20Pages-Live%20Portal-success?style=for-the-badge&logo=github)](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/)
[![Version](https://img.shields.io/badge/Version-v2.4%20Production-blue?style=for-the-badge)](https://github.com/iamshreeji-copy2/Sunscrap_Recyclers_Dashboard)
[![Tests](https://img.shields.io/badge/Automated%20Tests-100%25%20PASS-green?style=for-the-badge)](https://github.com/iamshreeji-copy2/Sunscrap_Recyclers_Dashboard)

---

## 🌐 Live Demonstration Portal
- **Live URL:** [https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/](https://iamshreeji-copy2.github.io/Sunscrap_Recyclers_Dashboard/)
- **Repository:** [https://github.com/iamshreeji-copy2/Sunscrap_Recyclers_Dashboard](https://github.com/iamshreeji-copy2/Sunscrap_Recyclers_Dashboard)

---

## 🔐 Station Login Credentials & Role Hierarchy

| Role | Username | Password | Key Permissions |
|---|---|---|---|
| **Lead Developer** | `developer` | `Dev@2026` | Full telemetry diagnostics, device signatures, browser/network audit log |
| **System Administrator** | `admin` | `Sunscrap@2026` | Full control, User Management (Add/Delete Users), Plant topology & threshold editor |
| **Plant Owner** | `darshan_owner` | `Owner@2026` | CapEx payback ROI tracker, revenue in INR (₹), expiring share links, plant metadata |
| **Third-Party Viewer / Commenter**| `viewer` | `Viewer@2026` | Sanitized telemetry dashboards, plant operations discussion notes, masked admin settings |

*Note: You can also use the 1-click credential presets provided directly on the sign-in screen.*

---

## 🚀 Key Features in Version v2.4

1. **Mandatory Login Gatekeeper:**
   - Unauthenticated visitors on GitHub Pages are immediately redirected to `login.html` before any dashboard data or charts can render.
   - Distinct **Sign Out** button in the header cleanly terminates session, clears credentials from `localStorage`, and logs a security audit event.

2. **Dual Switchable Dashboards:**
   - **⚡ Technical SCADA Dashboard:** Real-time engineering telemetry for 13 inverters, 2 MFMs, weather sensors (WMS), string currents, and dual-axis generation curves.
   - **📊 Analytical AI/ML Dashboard:** Data science analytics, financial revenue in INR, CapEx payback tracker (₹18.5 Cr investment vs ₹47.02 Lakhs recovered), 7-day predictive ML forecast with ±95% confidence intervals, irradiance-to-power regression ($R^2 = 0.982$), and loss breakdown waterfall.

3. **Interactive & Colorful ECharts with Explicit Axis Labels:**
   - Every single chart features explicit X and Y axis titles with units placed in the middle (`nameLocation: 'middle'`) and appropriate gap padding (`nameGap: 28-42px`).
   - Smooth animations with low-latency rendering and high-contrast accessibility options.

4. **Emergency Acoustic Siren & Strobe Overlay:**
   - High-priority emergency popup with dual-tone industrial acoustic siren synthesis using Web Audio API (oscillating 960Hz / 640Hz).
   - Exact incident specifications:
     - **Target Device:** `Inverter 08 (Inv-08 / 320 kWp)`
     - **Status Code:** `ERR-402 (Grid Under-voltage)`
     - **Event Timestamp:** `01:32:05 PM IST`
     - **Alarm State:** `ACTIVE / UNACKNOWLEDGED`
   - **"Go to Target Device"** button navigates directly to Inverter 08's active power curves, string currents, and telemetry tables.
   - **"Cancel & Silence Siren"** or clicking the top header Bell icon opens the complete **Alarm History Trail & Log Retrieval** modal.

5. **User Management Screen (Add & Delete Users):**
   - Under `System Settings > User Accounts`, Administrators can create new operator accounts with designated roles or delete existing users with instantaneous synchronization to backend database and browser storage.

6. **Developer Security & Telemetry Audit Trail:**
   - Under `System Settings > Security Audit`, developers can troubleshoot workstation issues by reviewing login and logout records containing:
     - Timestamp (IST)
     - Username & Assigned Role
     - Device Signature (e.g. Linux x86_64, Windows 11, Apple macOS)
     - Browser Engine & Version (e.g. Chrome 129, Firefox 131, Safari 17)
     - Approximate Location (Ahmedabad, Gujarat, India • 22.9868° N, 72.3787° E)
     - Network Provider / ISP (Jio Fiber High-Speed Gateway, Airtel Broadband, Corporate WAN)
     - Terminal IP Address

7. **Plant Discussion & Collaboration Feed:**
   - The fourth role (Third-Party Viewer / Commenter) and station engineers can post and review engineering remarks, maintenance observations, and audit notes.

8. **Frozen Sidebar & Floating Back-to-Top Button:**
   - The navigation sidebar stays fixed at 100vh height with smooth scroll.
   - Circular Back-to-Top floating button appears at bottom-right when scrolled down.

9. **Time-Limited Expiring Share Links:**
   - Generate temporary links valid for 1 hour, 24 hours, 7 days, 30 days, or custom expiry with granular privacy masking (mask revenue figures, mask raw string currents, mask administrative settings).

10. **Plant Specifications, Owner Details & GPS Location Editor:**
    - Live editable modal for Plant Name, AC/DC rating, Site Address, Owner Name, Contact Info, auto-detect GPS coordinates, and Google Maps pin.

---

## 🛠️ Local Development & Running

```bash
# 1. Enter website directory
cd /home/linux/Documents/Darshan_SCADA_Software_October_2026/Website_implimentaion

# 2. Start local Django development server
python3 manage.py runserver 0.0.0.0:8001

# 3. Access local instance in browser
# http://127.0.0.1:8001/login
```

## 📦 Building and Publishing Static GitHub Pages

```bash
# Compile dynamic Django views into static HTML distribution
python3 build_static_site.py

# Push to GitHub Pages repository
cd /home/linux/Documents/Darshan_SCADA_Software_October_2026/gh_pages_deploy
git add .
git commit -m "feat: Sunscrap SCADA v2.4 production release"
git push origin main
```
