import json
from django.db import models
from django.conf import settings
from apps.plant.models import Device

class DataQuality(models.TextChoices):
    VALID = 'valid', 'Valid'
    SUSPECT = 'suspect', 'Suspect'
    INVALID = 'invalid', 'Invalid'
    MISSING = 'missing', 'Missing'
    STALE = 'stale', 'Stale'
    ESTIMATED = 'estimated', 'Estimated'

class CommunicationStatus(models.TextChoices):
    ONLINE = 'online', 'Online'
    STALE = 'stale', 'Stale'
    OFFLINE = 'offline', 'Offline'
    UNKNOWN = 'unknown', 'Unknown'

class AlarmSeverity(models.TextChoices):
    CRITICAL = 'critical', 'Critical'
    MAJOR = 'major', 'Major'
    MINOR = 'minor', 'Minor'
    WARNING = 'warning', 'Warning'
    INFO = 'info', 'Info'

class InverterObservation(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='inverter_observations')
    timestamp = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)
    quality = models.CharField(max_length=20, choices=DataQuality.choices, default=DataQuality.VALID)
    
    # Base 19 inverter parameters
    vdc = models.FloatField(default=0.0, help_text="Total DC Voltage (V)")
    idc = models.FloatField(default=0.0, help_text="Total DC Current (A)")
    v_ry = models.FloatField(default=0.0, help_text="Grid Voltage R-Y (V)")
    v_yb = models.FloatField(default=0.0, help_text="Grid Voltage Y-B (V)")
    v_br = models.FloatField(default=0.0, help_text="Grid Voltage B-R (V)")
    i_r = models.FloatField(default=0.0, help_text="Phase R Current (A)")
    i_y = models.FloatField(default=0.0, help_text="Phase Y Current (A)")
    i_b = models.FloatField(default=0.0, help_text="Phase B Current (A)")
    power_factor = models.FloatField(default=0.99, help_text="Power Factor")
    frequency = models.FloatField(default=50.0, help_text="Grid Frequency (Hz)")
    active_power = models.FloatField(default=0.0, help_text="AC Active Power (kW)")
    reactive_power = models.FloatField(default=0.0, help_text="AC Reactive Power (kVAR)")
    dc_power = models.FloatField(default=0.0, help_text="Total DC Power (kW)")
    daily_yield = models.FloatField(default=0.0, help_text="Today Energy Yield (kWh)")
    lifetime_yield = models.FloatField(default=0.0, help_text="Lifetime Cumulative Energy (kWh)")
    insulation_resistance = models.FloatField(default=1000.0, help_text="Insulation Resistance (kOhm)")
    temperature = models.FloatField(default=45.0, help_text="Internal Inverter Temperature (°C)")
    operating_status = models.CharField(max_length=30, default="Running")
    alarm_code = models.CharField(max_length=50, blank=True, default="0")
    
    # 12 MPPT channels stored as JSON dict: {'v': [v1..v12], 'i': [i1..i12]}
    mppt_data = models.JSONField(default=dict, blank=True)
    # 25 String currents stored as JSON list: [s1..s25]
    string_currents = models.JSONField(default=list, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    @property
    def conversion_efficiency(self):
        """Instantaneous conversion efficiency 100 * P_AC / P_DC if positive DC power."""
        if self.dc_power and self.dc_power > 10.0 and self.active_power > 0:
            eff = (self.active_power / self.dc_power) * 100.0
            return round(min(eff, 99.5), 2)
        return None

    def get_mppt_voltages(self):
        return self.mppt_data.get('v', [0.0]*12)

    def get_mppt_currents(self):
        return self.mppt_data.get('i', [0.0]*12)

    def get_all_69_columns(self):
        """Returns ordered dict/list of all 69 standard inverter parameter values."""
        res = [
            ('timestamp', self.timestamp.strftime('%Y-%m-%d %H:%M:%S')),
            ('vdc', self.vdc),
            ('idc', self.idc),
            ('v_ry', self.v_ry),
            ('v_yb', self.v_yb),
            ('v_br', self.v_br),
            ('i_r', self.i_r),
            ('i_y', self.i_y),
            ('i_b', self.i_b),
            ('power_factor', self.power_factor),
            ('frequency', self.frequency),
            ('active_power', self.active_power),
            ('reactive_power', self.reactive_power),
            ('dc_power', self.dc_power),
            ('daily_yield', self.daily_yield),
            ('lifetime_yield', self.lifetime_yield),
            ('insulation_resistance', self.insulation_resistance),
            ('temperature', self.temperature),
            ('alarm_code', self.alarm_code),
            ('operating_status', self.operating_status),
        ]
        mv = self.get_mppt_voltages()
        mi = self.get_mppt_currents()
        for idx in range(12):
            res.append((f'mppt_{idx+1}_vdc', mv[idx] if idx < len(mv) else 0.0))
        for idx in range(12):
            res.append((f'mppt_{idx+1}_idc', mi[idx] if idx < len(mi) else 0.0))
        sc = self.string_currents or []
        for idx in range(25):
            res.append((f'string_{idx+1}_idc', sc[idx] if idx < len(sc) else 0.0))
        return res


class MFMObservation(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='mfm_observations')
    timestamp = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)
    quality = models.CharField(max_length=20, choices=DataQuality.choices, default=DataQuality.VALID)
    
    active_power = models.FloatField(default=0.0, help_text="Total Active Power (kW)")
    reactive_power = models.FloatField(default=0.0, help_text="Total Reactive Power (kVAR)")
    apparent_power = models.FloatField(default=0.0, help_text="Total Apparent Power (kVA)")
    v_ll = models.FloatField(default=0.0, help_text="Average Line-to-Line Voltage (kV)")
    v_ry = models.FloatField(default=0.0, help_text="Voltage R-Y (V)")
    v_yb = models.FloatField(default=0.0, help_text="Voltage Y-B (V)")
    v_br = models.FloatField(default=0.0, help_text="Voltage B-R (V)")
    i_r = models.FloatField(default=0.0, help_text="Current R (A)")
    i_y = models.FloatField(default=0.0, help_text="Current Y (A)")
    i_b = models.FloatField(default=0.0, help_text="Current B (A)")
    i_neutral = models.FloatField(default=0.0, help_text="Neutral Current (A)")
    frequency = models.FloatField(default=50.0, help_text="Frequency (Hz)")
    power_factor = models.FloatField(default=0.99, help_text="Power Factor")
    
    import_energy_today = models.FloatField(default=0.0, help_text="Today Imported Energy (kWh)")
    export_energy_today = models.FloatField(default=0.0, help_text="Today Exported Energy (kWh)")
    import_energy_lifetime = models.FloatField(default=0.0, help_text="Cumulative Imported Energy (kWh)")
    export_energy_lifetime = models.FloatField(default=0.0, help_text="Cumulative Exported Energy (kWh)")

    class Meta:
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']


class WMSObservation(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='wms_observations')
    timestamp = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)
    quality = models.CharField(max_length=20, choices=DataQuality.choices, default=DataQuality.VALID)
    
    ambient_temp = models.FloatField(default=30.0, help_text="Ambient Air Temperature (°C)")
    module_temp = models.FloatField(default=45.0, help_text="Back-of-Module Temperature (°C)")
    humidity = models.FloatField(default=40.0, help_text="Relative Humidity (%RH)")
    ghi = models.FloatField(default=0.0, help_text="Global Horizontal Irradiance (W/m²)")
    gti = models.FloatField(default=0.0, help_text="Global Tilted Irradiance (W/m²)")
    insolation_today_ghi = models.FloatField(default=0.0, help_text="Integrated Daily GHI (kWh/m²)")
    insolation_today_gti = models.FloatField(default=0.0, help_text="Integrated Daily GTI (kWh/m²)")
    wind_speed = models.FloatField(default=2.5, help_text="Wind Speed (m/s)")
    wind_direction = models.FloatField(default=180.0, help_text="Wind Direction (degrees)")
    diffuse_irradiance = models.FloatField(default=0.0, help_text="Diffuse Irradiance (W/m²)")
    rainfall = models.FloatField(default=0.0, help_text="Daily Rainfall (mm)")
    cloud_cover = models.FloatField(default=10.0, help_text="Cloud Cover Percentage (%)")

    class Meta:
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']


class DeviceLatest(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='latest_state')
    last_contact_time = models.DateTimeField()
    last_valid_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=CommunicationStatus.choices, default=CommunicationStatus.ONLINE)
    operating_state = models.CharField(max_length=30, default="Running")
    active_power = models.FloatField(default=0.0)
    daily_yield = models.FloatField(default=0.0)
    lifetime_yield = models.FloatField(default=0.0)
    temperature = models.FloatField(default=0.0)
    conversion_efficiency = models.FloatField(null=True, blank=True)
    alarm_active = models.BooleanField(default=False)
    latest_alarm_code = models.CharField(max_length=50, blank=True)
    latest_alarm_text = models.CharField(max_length=255, blank=True)
    raw_snapshot = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Latest: {self.device.device_id} - {self.status} ({self.active_power} kW)"


class AlarmEvent(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alarms')
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=AlarmSeverity.choices, default=AlarmSeverity.WARNING)
    fault_text = models.TextField(blank=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_time']

    @property
    def duration_seconds(self):
        from django.utils import timezone
        end = self.end_time or timezone.now()
        return int((end - self.start_time).total_seconds())

    def __str__(self):
        return f"Alarm [{self.severity.upper()}] {self.device.device_id} - {self.code}: {self.description}"


class CommunicationEvent(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='comm_events')
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CommunicationStatus.choices)
    quality = models.CharField(max_length=20, choices=DataQuality.choices, default=DataQuality.VALID)
    duration_seconds = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_time']


class Rollup(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='rollups')
    resolution = models.CharField(max_length=20, choices=[
        ('15min', '15 Minutes'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('monthly', 'Monthly')
    ])
    bucket_start = models.DateTimeField(db_index=True)
    bucket_end = models.DateTimeField()
    metric_id = models.CharField(max_length=64, db_index=True)
    value = models.FloatField(default=0.0)
    min_val = models.FloatField(null=True, blank=True)
    max_val = models.FloatField(null=True, blank=True)
    sum_val = models.FloatField(null=True, blank=True)
    count_val = models.IntegerField(default=0)
    coverage_pct = models.FloatField(default=100.0)

    class Meta:
        indexes = [
            models.Index(fields=['device', 'metric_id', 'resolution', 'bucket_start']),
            models.Index(fields=['metric_id', 'resolution', 'bucket_start']),
        ]
        ordering = ['bucket_start']


class RawIngestBatch(models.Model):
    collector_id = models.CharField(max_length=100)
    schema_version = models.CharField(max_length=20, default="1.0")
    batch_sequence = models.BigIntegerField(default=1)
    payload_hash = models.CharField(max_length=64, unique=True)
    payload = models.JSONField()
    status = models.CharField(max_length=20, default="ACCEPTED")
    received_at = models.DateTimeField(auto_now_add=True)
