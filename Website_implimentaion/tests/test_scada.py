import json
import os
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User, UserRole, EmailOTP, PasswordResetToken
from apps.plant.models import Plant, Device, DeviceType
from apps.telemetry.models import InverterObservation, MFMObservation, WMSObservation, DeviceLatest
from apps.telemetry.services import PlantCalculations, seed_reference_telemetry
from apps.exports.models import ReportSnapshot, ExportJob, ExportFormat
from apps.exports.services import generate_csv, generate_xlsx, generate_pdf, sanitize_csv_cell

class ScadaCoreTestSuite(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='test_admin', password='TestAdmin@2026', email='admin@test.local', role=UserRole.ADMINISTRATOR
        )
        self.viewer = User.objects.create_user(
            username='test_viewer', password='TestViewer@2026', email='viewer@test.local', role=UserRole.VIEWER
        )
        seed_reference_telemetry()

    def test_scientific_calculations(self):
        # Sanity test from specifications:
        # 11,921.30 kWh / 4,640 kWp = ~2.57 kWh/kWp
        sp_yield = PlantCalculations.specific_yield(11921.30, 4640.0)
        self.assertEqual(sp_yield, 2.57)

        # Full-day 24h CUF for 3,900 kW AC:
        # 100 * 11921.30 / (3900 * 24) = ~12.74%
        cuf = PlantCalculations.cuf(11921.30, 3900.0, 24.0)
        self.assertEqual(cuf, 12.74)

        # PR with GTI insolation 5.94 kWh/m²:
        # 100 * 11921.30 / (4640 * 5.94) = ~43.25%
        pr = PlantCalculations.pr(11921.30, 4640.0, 5.94)
        self.assertIsNotNone(pr)
        self.assertTrue(0 < pr < 100)

        # Inverter conversion efficiency
        inv = InverterObservation.objects.first()
        self.assertIsNotNone(inv.conversion_efficiency)
        self.assertTrue(90.0 < inv.conversion_efficiency < 100.0)

    def test_authentication_and_login(self):
        # Failed login
        resp = self.client.post(reverse('login'), {'username': 'test_admin', 'password': 'WrongPassword'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')

        # Successful login
        resp = self.client.post(reverse('login'), {'username': 'test_admin', 'password': 'TestAdmin@2026'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/dashboard', resp.url)

    def test_otp_flow_and_limits(self):
        otp_obj, raw_code = EmailOTP.create_otp(self.admin, self.admin.email)
        self.assertEqual(len(raw_code), 6)
        
        # Test wrong OTP increments attempts
        success, msg = otp_obj.verify('999999')
        self.assertFalse(success)
        self.assertEqual(otp_obj.attempts, 1)

        # Test valid OTP
        success, msg = otp_obj.verify(raw_code)
        self.assertTrue(success)
        self.assertTrue(otp_obj.is_used)

        # Re-use fails
        re_success, re_msg = otp_obj.verify(raw_code)
        self.assertFalse(re_success)

    def test_password_reset_token(self):
        token = PasswordResetToken.create_token(self.admin)
        self.assertTrue(token.is_valid())
        
        resp = self.client.get(reverse('reset_password', args=[token.token]))
        self.assertEqual(resp.status_code, 200)

    def test_all_routes_accessible(self):
        self.client.login(username='test_admin', password='TestAdmin@2026')
        routes = [
            'dashboard',
            'inverter_overview',
            'mfm_overview',
            'report_summary',
            'report_energy_generation',
            'report_inverter_generation',
            'report_alarm',
            'report_trends',
            'report_custom',
            'report_inverter_parameter',
            'report_mfm_parameter',
            'report_wms_parameter',
            'report_communication',
            'alert_logs',
            'downloads',
            'schedules',
            'profile',
            'profile_email',
            'plant_settings',
            'devices_settings',
            'notifications_settings',
            'branding_settings',
            'system_health',
            'audit_logs',
        ]
        for r_name in routes:
            resp = self.client.get(reverse(r_name))
            self.assertEqual(resp.status_code, 200, f"Route {r_name} failed with status {resp.status_code}")

    def test_export_contract(self):
        # Test formula injection defense
        self.assertEqual(sanitize_csv_cell("=1+1"), "'=1+1")
        self.assertEqual(sanitize_csv_cell("+cmd"), "'+cmd")
        self.assertEqual(sanitize_csv_cell(123.45), "123.45")

        # Create dummy snapshot
        cols = [{'key': 'time', 'label': 'Time'}, {'key': 'power', 'label': 'Power (kW)'}]
        rows = [{'time': '12:00', 'power': 288.5}, {'time': '12:15', 'power': 291.2}]
        snap = ReportSnapshot.objects.create(
            report_type='test', title='Test Report', period_label='Today', interval_label='15m',
            data_as_of=timezone.now(), row_count=2, columns=cols, rows_data=rows
        )

        tmp_csv = '/tmp/test_export.csv'
        tmp_xlsx = '/tmp/test_export.xlsx'
        tmp_pdf = '/tmp/test_export.pdf'

        # CSV
        size_csv, chk_csv = generate_csv(snap, tmp_csv)
        self.assertTrue(size_csv > 0)
        self.assertTrue(os.path.exists(tmp_csv))

        # XLSX
        size_xlsx, chk_xlsx = generate_xlsx(snap, tmp_xlsx)
        self.assertTrue(size_xlsx > 0)
        self.assertTrue(os.path.exists(tmp_xlsx))

        # PDF
        size_pdf, chk_pdf = generate_pdf(snap, tmp_pdf)
        self.assertTrue(size_pdf > 0)
        self.assertTrue(os.path.exists(tmp_pdf))

        # Cleanup
        for p in (tmp_csv, tmp_xlsx, tmp_pdf):
            if os.path.exists(p): os.remove(p)

    def test_collector_batch_ingest_api(self):
        payload = {
            'collector_id': 'gateway-unit-test',
            'sequence': 1001,
            'records': [
                {
                    'device_id': 'INV-01',
                    'timestamp': timezone.now().isoformat(),
                    'active_power': 285.5,
                    'daily_yield': 915.2,
                    'dc_power': 290.0,
                    'temperature': 46.2,
                    'operating_status': 'Running'
                }
            ]
        }
        resp = self.client.post(
            reverse('ingest_batch'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['status'], 'ACCEPTED')
        self.assertEqual(data['records_processed'], 1)

        # Test idempotency replay
        resp_replay = self.client.post(
            reverse('ingest_batch'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp_replay.status_code, 200)
        self.assertIn('Duplicate batch', resp_replay.json()['message'])
