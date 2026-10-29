"""
Django Management Command: run_mqtt_bridge
Starts the background MQTT Telemetry Bridge connecting to the EMQX Cloud Broker.
Usage:
    python3 manage.py run_mqtt_bridge --host cXXXXX.emqx.cloud --port 8883
"""

from django.core.management.base import BaseCommand
from apps.telemetry.mqtt_bridge import ScadaMqttBridge, DEFAULT_BROKER_HOST, DEFAULT_BROKER_PORT, DEFAULT_USERNAME, DEFAULT_PASSWORD, DEFAULT_TOPIC

class Command(BaseCommand):
    help = 'Runs the live MQTT Telemetry Bridge subscriber to ingest datalogger streams from EMQX Cloud'

    def add_arguments(self, parser):
        parser.add_argument('--host', type=str, default=DEFAULT_BROKER_HOST, help='MQTT Broker Hostname')
        parser.add_argument('--port', type=int, default=DEFAULT_BROKER_PORT, help='MQTT Broker Port (default: 8883 for TLS)')
        parser.add_argument('--username', type=str, default=DEFAULT_USERNAME, help='MQTT Username')
        parser.add_argument('--password', type=str, default=DEFAULT_PASSWORD, help='MQTT Password')
        parser.add_argument('--topic', type=str, default=DEFAULT_TOPIC, help='MQTT Telemetry Topic')
        parser.add_argument('--no-tls', action='store_true', help='Disable TLS (only for unencrypted port 1883)')

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        username = options['username']
        password = options['password']
        topic = options['topic']
        use_tls = not options['no_tls']

        self.stdout.write(self.style.SUCCESS(f"==========================================================="))
        self.stdout.write(self.style.SUCCESS(f" Starting Sunscrap SCADA MQTT Ingestion Bridge"))
        self.stdout.write(self.style.SUCCESS(f" Host: {host}:{port} | TLS: {use_tls}"))
        self.stdout.write(self.style.SUCCESS(f" User: {username} | Topic: {topic}"))
        self.stdout.write(self.style.SUCCESS(f"==========================================================="))

        bridge = ScadaMqttBridge(
            host=host,
            port=port,
            username=username,
            password=password,
            topic=topic,
            use_tls=use_tls
        )
        try:
            bridge.start()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("MQTT Bridge interrupted by operator."))
            bridge.stop()
