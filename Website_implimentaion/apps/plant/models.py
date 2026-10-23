from django.db import models

class DeviceType(models.TextChoices):
    INVERTER = 'inverter', 'Solar Inverter'
    MFM = 'mfm', 'Multi-Function Meter (MFM)'
    WMS = 'wms', 'Weather Monitoring Station (WMS)'

class Plant(models.Model):
    name = models.CharField(max_length=150, default="SATs Solar Plant")
    organization = models.CharField(max_length=150, default="SATs (Semiconductor Analysis and Testing Solutions)")
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    ac_capacity_kw = models.FloatField(default=3900.0, help_text="Total plant AC rated capacity in kW")
    dc_capacity_kwp = models.FloatField(default=4640.0, help_text="Total plant DC peak capacity in kWp")
    latitude = models.FloatField(default=23.0225)
    longitude = models.FloatField(default=72.5714)
    expected_daily_yield_kwh = models.FloatField(default=18500.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.organization}) - {self.ac_capacity_kw} kW AC / {self.dc_capacity_kwp} kWp DC"


class Device(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=50, unique=True, help_text="INV-01 .. INV-13, MFM-LT, MFM-OUT, WMS-01")
    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DeviceType.choices)
    manufacturer = models.CharField(max_length=100, default="Sungrow")
    model = models.CharField(max_length=100, default="SG300HX")
    zone = models.CharField(max_length=50, default="Main Field")
    ac_capacity_kw = models.FloatField(default=300.0, help_text="Independently configured AC capacity kW")
    dc_capacity_kwp = models.FloatField(default=356.92, help_text="Independently configured DC capacity kWp")
    is_enabled = models.BooleanField(default=True)
    poll_interval_seconds = models.IntegerField(default=30)
    stale_threshold_seconds = models.IntegerField(default=120)
    offline_threshold_seconds = models.IntegerField(default=300)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'device_id']

    def __str__(self):
        return f"{self.device_id}: {self.name} ({self.get_device_type_display()})"


class MetricKind(models.TextChoices):
    GAUGE = 'gauge', 'Gauge (Instantaneous Value)'
    COUNTER = 'counter', 'Counter (Cumulative Value)'
    STATUS = 'status', 'Status / Code'

class MetricDefinition(models.Model):
    metric_id = models.CharField(max_length=64, unique=True, help_text="Standardized ID e.g. active_power, daily_yield")
    label = models.CharField(max_length=100)
    unit = models.CharField(max_length=30, blank=True)
    device_type = models.CharField(max_length=20, choices=DeviceType.choices, blank=True, null=True)
    kind = models.CharField(max_length=20, choices=MetricKind.choices, default=MetricKind.GAUGE)
    precision = models.IntegerField(default=2)
    valid_min = models.FloatField(null=True, blank=True)
    valid_max = models.FloatField(null=True, blank=True)
    aggregation_method = models.CharField(max_length=20, default="avg", choices=[
        ('sum', 'Sum'),
        ('avg', 'Average'),
        ('max', 'Maximum'),
        ('min', 'Minimum'),
        ('last', 'Last Value'),
        ('diff', 'Difference (Counter)')
    ])
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['metric_id']

    def __str__(self):
        return f"{self.metric_id} ({self.label}) [{self.unit}]"
