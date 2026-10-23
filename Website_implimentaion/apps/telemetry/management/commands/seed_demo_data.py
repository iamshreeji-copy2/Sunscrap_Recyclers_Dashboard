from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.telemetry.services import seed_plant_and_devices, seed_reference_telemetry, seed_historical_telemetry
from apps.accounts.models import UserRole

class Command(BaseCommand):
    help = 'Seeds initial users, plant devices, reference telemetry, and historical interval curves.'

    def add_arguments(self, parser):
        parser.add_argument('--admin-user', default='admin', help='Admin username')
        parser.add_argument('--admin-pass', default='Sunscrap@2026', help='Admin password')
        parser.add_argument('--admin-email', default='admin@sunscrap.local', help='Admin email')

    def handle(self, *args, **options):
        User = get_user_model()
        admin_u = options['admin_user']
        admin_p = options['admin_pass']
        admin_e = options['admin_email']

        # 1. Admin user
        user, created = User.objects.get_or_create(
            username=admin_u,
            defaults={
                'email': admin_e,
                'role': UserRole.ADMINISTRATOR,
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Plant',
                'last_name': 'Administrator',
            }
        )
        if created or not user.check_password(admin_p):
            user.set_password(admin_p)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created/Updated Administrator account '{admin_u}'"))

        # 2. Operator / Viewer user
        viewer, v_created = User.objects.get_or_create(
            username='viewer',
            defaults={
                'email': 'viewer@sunscrap.local',
                'role': UserRole.VIEWER,
                'is_staff': False,
                'is_superuser': False,
                'first_name': 'Control Room',
                'last_name': 'Operator',
            }
        )
        if v_created or not viewer.check_password('Viewer@2026'):
            viewer.set_password('Viewer@2026')
            viewer.save()
            self.stdout.write(self.style.SUCCESS("Created/Updated Viewer account 'viewer' (password: Viewer@2026)"))

        # 3. Topology & reference telemetry
        self.stdout.write("Initializing topology and seeding reference telemetry...")
        seed_reference_telemetry()
        
        # 4. Historical interval data for charts & reports
        self.stdout.write("Generating continuous interval time series for charts...")
        seed_historical_telemetry(days=1)

        self.stdout.write(self.style.SUCCESS("SATs Solar SCADA database successfully seeded and operational!"))
