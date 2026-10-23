from django.db import models
from django.conf import settings

class CustomReportConfiguration(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    device_ids = models.JSONField(default=list, help_text="List of selected device IDs")
    metric_ids = models.JSONField(default=list, help_text="List of allowlisted metric IDs")
    column_order = models.JSONField(default=list)
    aggregation = models.CharField(max_length=20, default='avg', choices=[
        ('avg', 'Average'),
        ('sum', 'Sum'),
        ('max', 'Maximum'),
        ('min', 'Minimum'),
        ('last', 'Last Value')
    ])
    default_period = models.CharField(max_length=20, default='daily', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Range'),
        ('yearly', 'Yearly')
    ])
    default_interval = models.CharField(max_length=20, default='15min', choices=[
        ('raw', 'Raw'),
        ('15min', '15 Minutes'),
        ('hourly', '1 Hour'),
        ('daily', 'Daily')
    ])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TrendConfiguration(models.Model):
    panel_index = models.IntegerField(default=1, choices=[(1, 'Panel 1'), (2, 'Panel 2'), (3, 'Panel 3'), (4, 'Panel 4')])
    title = models.CharField(max_length=150, default="Trend Chart")
    device_id = models.CharField(max_length=50, default="INV-01")
    metric_id = models.CharField(max_length=50, default="active_power")
    chart_type = models.CharField(max_length=20, default="line", choices=[
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('area', 'Area Chart')
    ])
    period = models.CharField(max_length=20, default="daily")
    interval = models.CharField(max_length=20, default="15min")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['panel_index']

    def __str__(self):
        return f"Trend Panel {self.panel_index}: {self.title} ({self.device_id} - {self.metric_id})"
