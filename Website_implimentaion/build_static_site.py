import os
import re
import shutil
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:8001"
OUTPUT_DIR = "/home/linux/Documents/Darshan_SCADA_Software_October_2026/gh_pages_deploy"

PAGES = [
    ("/dashboard", "index.html"),
    ("/dashboard/analytical", "dashboard_analytical.html"),
    ("/inverters/overview", "inverter_overview.html"),
    ("/mfm/overview", "mfm_overview.html"),
    ("/reports/summary", "report_summary.html"),
    ("/reports/energy/generation", "report_energy_generation.html"),
    ("/reports/inverter/generation", "report_inverter_generation.html"),
    ("/reports/alarm", "report_alarm.html"),
    ("/reports/alarm-logs", "alert_logs.html"),
    ("/reports/trends", "report_trends.html"),
    ("/reports/custom-report", "report_custom.html"),
    ("/reports/inverter/parameter", "report_inverter_parameter.html"),
    ("/reports/mfm/parameter", "report_mfm_parameter.html"),
    ("/reports/wms/parameter", "report_wms_parameter.html"),
    ("/reports/communication", "report_communication.html"),
    ("/reports/downloads", "downloads.html"),
    ("/reports/schedules", "schedules.html"),
    ("/settings/users", "users_settings.html"),
    ("/settings/audit", "audit.html"),
    ("/settings/plant", "plant_settings.html"),
    ("/settings/devices", "devices_settings.html"),
    ("/settings/system-health", "system_health.html"),
    ("/profile", "profile.html"),
    ("/login", "login.html"),
    ("/login/otp", "login_otp.html"),
    ("/forgot/password", "forgot_password.html"),
]

URL_REPLACEMENTS = [
    (r'href="/dashboard/analytical"', 'href="./dashboard_analytical.html"'),
    (r'href="/dashboard"', 'href="./index.html"'),
    (r'href="/home"', 'href="./index.html"'),
    (r'href="/inverters/overview"', 'href="./inverter_overview.html"'),
    (r'href="/mfm/overview"', 'href="./mfm_overview.html"'),
    (r'href="/reports/summary"', 'href="./report_summary.html"'),
    (r'href="/reports/energy/generation"', 'href="./report_energy_generation.html"'),
    (r'href="/reports/inverter/generation"', 'href="./report_inverter_generation.html"'),
    (r'href="/reports/alarm"', 'href="./report_alarm.html"'),
    (r'href="/reports/alarm-logs"', 'href="./alert_logs.html"'),
    (r'href="/reports/trends"', 'href="./report_trends.html"'),
    (r'href="/reports/custom-report"', 'href="./report_custom.html"'),
    (r'href="/reports/inverter/parameter"', 'href="./report_inverter_parameter.html"'),
    (r'href="/reports/mfm/parameter"', 'href="./report_mfm_parameter.html"'),
    (r'href="/reports/wms/parameter"', 'href="./report_wms_parameter.html"'),
    (r'href="/reports/communication"', 'href="./report_communication.html"'),
    (r'href="/reports/downloads"', 'href="./downloads.html"'),
    (r'href="/reports/schedules"', 'href="./schedules.html"'),
    (r'href="/settings/users"', 'href="./users_settings.html"'),
    (r'href="/settings/audit"', 'href="./audit.html"'),
    (r'href="/settings/plant"', 'href="./plant_settings.html"'),
    (r'href="/settings/devices"', 'href="./devices_settings.html"'),
    (r'href="/settings/system-health"', 'href="./system_health.html"'),
    (r'href="/profile"', 'href="./profile.html"'),
    (r'href="/login"', 'href="./login.html"'),
    (r'href="/logout"', 'href="./login.html"'),
    (r'href="/login/otp"', 'href="./login_otp.html"'),
    (r'href="/forgot/password"', 'href="./forgot_password.html"'),
    (r'href="/static/', 'href="./static/'),
    (r'src="/static/', 'src="./static/'),
    (r'data-src="/static/', 'data-src="./static/'),
    (r"url\('/static/", "url('./static/"),
    (r'url\("/static/', 'url("./static/'),
    (r'action="/login"', 'action="./index.html"'),
]

def main():
    print(f"Building static distribution in {OUTPUT_DIR}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Clean output dir while preserving .git
    for item in os.listdir(OUTPUT_DIR):
        if item == '.git':
            continue
        p = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)

    # 1. Setup cookie jar & login
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # Get CSRF
    resp = opener.open(f"{BASE_URL}/login")
    login_html = resp.read().decode('utf-8')
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_html)
    csrf_token = csrf_match.group(1) if csrf_match else ""

    # Login POST
    login_data = urllib.parse.urlencode({
        'csrfmiddlewaretoken': csrf_token,
        'username': 'admin',
        'password': 'SATs@2026',
        'remember_me': 'on'
    }).encode('utf-8')
    opener.open(f"{BASE_URL}/login", data=login_data)
    print("✓ Successfully authenticated with local SCADA engine")

    # 2. Fetch and adapt each page
    for route, filename in PAGES:
        url = f"{BASE_URL}{route}"
        try:
            # Use unauthenticated connection for auth screens so Django does not redirect to dashboard
            if filename in ('login.html', 'login_otp.html', 'forgot_password.html'):
                req = urllib.request.urlopen(url)
            else:
                req = opener.open(url)
            html = req.read().decode('utf-8')

            # Apply relative URL replacements
            for pattern, repl in URL_REPLACEMENTS:
                html = re.sub(pattern, repl, html)

            # In static mode, intercept ?export= links to trigger in-browser client-side download
            html = html.replace('href="?export=csv"', 'href="#" class="export-btn btn-client-csv"')
            html = html.replace('href="?export=xlsx"', 'href="#" class="export-btn btn-client-xlsx"')
            html = html.replace('href="?export=pdf"', 'href="#" class="export-btn btn-client-pdf"')

            out_path = os.path.join(OUTPUT_DIR, filename)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✓ Rendered {route} -> {filename}")
        except Exception as e:
            print(f"✗ Error rendering {route}: {e}")

    # 3. Copy static assets
    src_static = "/home/linux/Documents/Darshan_SCADA_Software_October_2026/Website_implimentaion/static"
    dst_static = os.path.join(OUTPUT_DIR, "static")
    shutil.copytree(src_static, dst_static)
    print("✓ Copied all static assets, CSS, JS, brand assets, and vendored ECharts")

    # 4. Copy README, CHECKPOINT, .gitignore & previous_coding_prompt.txt
    if os.path.exists("/home/linux/Documents/Darshan_SCADA_Software_October_2026/Website_implimentaion/.gitignore"):
        shutil.copy(
            "/home/linux/Documents/Darshan_SCADA_Software_October_2026/Website_implimentaion/.gitignore",
            os.path.join(OUTPUT_DIR, ".gitignore")
        )
    shutil.copy(
        "/home/linux/Documents/Darshan_SCADA_Software_October_2026/Website_implimentaion/README.md",
        os.path.join(OUTPUT_DIR, "README.md")
    )
    shutil.copy(
        "/home/linux/Documents/Darshan_SCADA_Software_October_2026/Website_implimentaion/CHECKPOINT.md",
        os.path.join(OUTPUT_DIR, "CHECKPOINT.md")
    )
    if os.path.exists("/home/linux/Documents/Darshan_SCADA_Software_October_2026/previous_coding_prompt.txt"):
        shutil.copy(
            "/home/linux/Documents/Darshan_SCADA_Software_October_2026/previous_coding_prompt.txt",
            os.path.join(OUTPUT_DIR, "previous_coding_prompt.txt")
        )

    # 5. Add .nojekyll for GitHub Pages
    with open(os.path.join(OUTPUT_DIR, ".nojekyll"), "w") as f:
        f.write("")
    print("✓ Created .nojekyll for GitHub Pages static serving")

    # 6. Copy root favicon files for browser discovery
    fav_src = os.path.join(src_static, "assets", "favicon.ico")
    if os.path.exists(fav_src):
        shutil.copy(fav_src, os.path.join(OUTPUT_DIR, "favicon.ico"))
    fav_svg = os.path.join(src_static, "assets", "favicon.svg")
    if os.path.exists(fav_svg):
        shutil.copy(fav_svg, os.path.join(OUTPUT_DIR, "favicon.svg"))
    fav_png = os.path.join(src_static, "assets", "favicon.png")
    if os.path.exists(fav_png):
        shutil.copy(fav_png, os.path.join(OUTPUT_DIR, "favicon.png"))
    print("✓ Deployed root favicon.ico, favicon.svg, and favicon.png")

    # 6. Mirror complete Django project source into Website_implimentaion/
    dst_django = os.path.join(OUTPUT_DIR, "Website_implimentaion")
    os.makedirs(dst_django, exist_ok=True)
    os.system(f"rsync -av --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' /home/linux/Documents/Darshan_SCADA_Software_October_2026/Website_implimentaion/ {dst_django}/")
    print("✓ Bundled full Django application source into Website_implimentaion/")

    print("\nStatic site build complete!")

if __name__ == '__main__':
    main()
