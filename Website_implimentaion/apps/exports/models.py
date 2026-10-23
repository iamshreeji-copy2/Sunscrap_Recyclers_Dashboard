import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone

class ExportFormat(models.TextChoices):
    XLSX = 'xlsx', 'Excel Spreadsheet (.xlsx)'
    CSV = 'csv', 'Comma Separated Values (.csv)'
    PDF = 'pdf', 'Portable Document Format (.pdf)'
    COPY = 'copy', 'Tab Separated Clipboard (TSV)'
    PRINT = 'print', 'Printable Layout'
    EMAIL = 'email', 'Email Delivery'

class JobStatus(models.TextChoices):
    QUEUED = 'queued', 'Queued'
    RUNNING = 'running', 'Running'
    READY = 'ready', 'Ready'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'

class ReportSnapshot(models.Model):
    snapshot_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=200)
    period_label = models.CharField(max_length=100)
    interval_label = models.CharField(max_length=50)
    data_as_of = models.DateTimeField()
    generated_at = models.DateTimeField(auto_now_add=True)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    row_count = models.IntegerField(default=0)
    columns = models.JSONField(default=list, help_text="List of {key, label, unit}")
    rows_data = models.JSONField(default=list, help_text="Canonical frozen rows data")
    summary_totals = models.JSONField(default=dict, blank=True)
    hash_sha256 = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.title} - {self.period_label} ({self.row_count} rows) [{self.snapshot_id}]"


class ExportJob(models.Model):
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(ReportSnapshot, on_delete=models.CASCADE, related_name='export_jobs')
    export_format = models.CharField(max_length=20, choices=ExportFormat.choices)
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.QUEUED)
    progress_pct = models.IntegerField(default=0)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_downloadable(self):
        return self.status == JobStatus.READY and self.file_path and timezone.now() <= self.expires_at

    def __str__(self):
        return f"ExportJob {self.job_id}: {self.export_format.upper()} - {self.status}"


class ReportSchedule(models.Model):
    name = models.CharField(max_length=150)
    report_type = models.CharField(max_length=64)
    period = models.CharField(max_length=20, choices=[
        ('daily', 'Daily (Previous Day)'),
        ('weekly', 'Weekly (Prior Mon-Sun)'),
        ('monthly', 'Monthly (Prior Month)'),
    ], default='daily')
    interval = models.CharField(max_length=20, default='15min')
    recipients = models.TextField(help_text="Comma-separated email addresses")
    export_format = models.CharField(max_length=20, choices=ExportFormat.choices, default=ExportFormat.XLSX)
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schedule: {self.name} ({self.get_period_display()})"
