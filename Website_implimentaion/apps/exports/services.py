import os
import csv
import io
import hashlib
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from .models import ExportJob, ReportSnapshot, JobStatus, ExportFormat

def sanitize_csv_cell(val):
    """Mitigates formula injection in spreadsheets by escaping leading '=', '+', '-', '@' characters."""
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{s}"
    return s


def generate_csv(snapshot, file_path):
    """Generates standard UTF-8 CSV with RFC 4180 compatibility."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header comments / Metadata
        writer.writerow([f"# SATs Solar SCADA - {snapshot.title}"])
        writer.writerow([f"# Period: {snapshot.period_label} | Generated: {snapshot.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([])
        
        # Column headers
        headers = [col.get('label', col.get('key')) for col in snapshot.columns]
        keys = [col.get('key') for col in snapshot.columns]
        writer.writerow(headers)
        
        # Data rows
        for row in snapshot.rows_data:
            line = [sanitize_csv_cell(row.get(k, '')) for k in keys]
            writer.writerow(line)
            
    # Compute size and hash
    size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        chk = hashlib.sha256(f.read()).hexdigest()
    return size, chk


def generate_xlsx(snapshot, file_path):
    """Generates genuine .xlsx with typed numeric cells, styles, auto-width, and metadata worksheet."""
    import xlsxwriter
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    workbook = xlsxwriter.Workbook(file_path, {'constant_memory': False})
    
    # Formats
    title_fmt = workbook.add_format({
        'bold': True, 'font_size': 14, 'font_color': '#0D1A36', 'align': 'left'
    })
    meta_fmt = workbook.add_format({'font_size': 9, 'font_color': '#617086'})
    header_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#0D1A36', 'font_color': '#FFFFFF',
        'border': 1, 'align': 'center', 'valign': 'vcenter'
    })
    num_fmt = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'align': 'right'})
    int_fmt = workbook.add_format({'num_format': '#,##0', 'border': 1, 'align': 'right'})
    text_fmt = workbook.add_format({'border': 1, 'align': 'left'})
    
    # Sheet 1: Report Data
    ws = workbook.add_worksheet('Telemetry Data')
    ws.write(0, 0, f"SATs Solar SCADA — {snapshot.title}", title_fmt)
    ws.write(1, 0, f"Period: {snapshot.period_label} | Scope: {snapshot.interval_label} | Generated: {snapshot.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", meta_fmt)
    
    keys = [col.get('key') for col in snapshot.columns]
    headers = [col.get('label', col.get('key')) for col in snapshot.columns]
    
    # Write table headers at row 3
    for col_idx, h in enumerate(headers):
        ws.write(3, col_idx, h, header_fmt)
        
    col_widths = [len(h) + 4 for h in headers]
    
    for row_idx, row in enumerate(snapshot.rows_data):
        current_r = 4 + row_idx
        for col_idx, k in enumerate(keys):
            val = row.get(k)
            if isinstance(val, (int, float)):
                ws.write_number(current_r, col_idx, val, num_fmt if isinstance(val, float) else int_fmt)
            else:
                ws.write_string(current_r, col_idx, str(val) if val is not None else '', text_fmt)
            
            s_len = len(str(val)) if val is not None else 0
            if s_len + 2 > col_widths[col_idx]:
                col_widths[col_idx] = min(s_len + 3, 40)
                
    for col_idx, w in enumerate(col_widths):
        ws.set_column(col_idx, col_idx, max(w, 12))
        
    # Sheet 2: Metadata & Quality
    ws_meta = workbook.add_worksheet('Metadata & Quality')
    ws_meta.write(0, 0, 'Report Metadata & Quality Audit', title_fmt)
    meta_rows = [
        ('Report Title', snapshot.title),
        ('Report Type', snapshot.report_type),
        ('Period Scope', snapshot.period_label),
        ('Interval Resolution', snapshot.interval_label),
        ('Data As Of (UTC/Local)', str(snapshot.data_as_of)),
        ('Snapshot ID', str(snapshot.snapshot_id)),
        ('Total Filtered Rows', snapshot.row_count),
        ('Plant Name', 'SATs Solar Plant'),
        ('Organization', 'SATs (Semiconductor Analysis and Testing Solutions)'),
        ('Configured AC Capacity', '3,900 kW'),
        ('Configured DC Capacity', '4,640 kWp'),
        ('Plant Timezone', 'Asia/Kolkata'),
        ('Quality Standard', 'IEC 61724-1 Standard Compliance'),
    ]
    for r_idx, (lbl, v) in enumerate(meta_rows):
        ws_meta.write(2 + r_idx, 0, lbl, header_fmt)
        ws_meta.write(2 + r_idx, 1, str(v), text_fmt)
    ws_meta.set_column(0, 0, 25)
    ws_meta.set_column(1, 1, 45)
    
    workbook.close()
    
    size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        chk = hashlib.sha256(f.read()).hexdigest()
    return size, chk


def generate_pdf(snapshot, file_path):
    """Generates server-side PDF with landscape layout, header repetition, and pagination."""
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Use landscape for tabular reports
    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(letter),
        leftMargin=25, rightMargin=25, topMargin=25, bottomMargin=25
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#0D1A36')
    )
    meta_style = ParagraphStyle(
        'DocMeta', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#617086')
    )
    th_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.white, alignment=1
    )
    cell_style = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=6.5, leading=8, textColor=colors.HexColor('#17243A')
    )
    
    elements = []
    
    # Title & Metadata
    elements.append(Paragraph(f"SATS SOLAR SCADA — {snapshot.title.upper()}", title_style))
    elements.append(Paragraph(
        f"Plant: SATs (Semiconductor Analysis and Testing Solutions) (3900 kW AC / 4640 kWp DC) | Period: {snapshot.period_label} | Generated: {snapshot.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        meta_style
    ))
    elements.append(Spacer(1, 10))
    
    # Select columns (if > 12 columns, pick first 10 for legible PDF presentation + mention full export in XLSX)
    cols = snapshot.columns
    if len(cols) > 12:
        cols_to_render = cols[:10]
        note = " (Showing first 10 columns in PDF layout; complete 69 parameters available via Excel / CSV)"
    else:
        cols_to_render = cols
        note = ""
        
    table_data = []
    header_row = [Paragraph(c.get('label', c.get('key'))[:16], th_style) for c in cols_to_render]
    table_data.append(header_row)
    
    keys = [c.get('key') for c in cols_to_render]
    # Limit rows to first 150 for PDF page sanity
    for row in snapshot.rows_data[:150]:
        r_cells = [Paragraph(str(row.get(k, '')), cell_style) for k in keys]
        table_data.append(r_cells)
        
    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D1A36')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t)
    
    if note:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Notice:</b>{note}", meta_style))
        
    doc.build(elements)
    
    size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        chk = hashlib.sha256(f.read()).hexdigest()
    return size, chk


def generate_copy_tsv(snapshot):
    """Generates tab-separated text string for direct clipboard copy."""
    lines = []
    headers = [col.get('label', col.get('key')) for col in snapshot.columns]
    keys = [col.get('key') for col in snapshot.columns]
    lines.append("\t".join(headers))
    
    for row in snapshot.rows_data:
        vals = [str(row.get(k, '')) for k in keys]
        lines.append("\t".join(vals))
        
    return "\n".join(lines)


def process_export_job(job):
    """Executes the export job according to requested format."""
    job.status = JobStatus.RUNNING
    job.progress_pct = 25
    job.save(update_fields=['status', 'progress_pct'])
    
    out_dir = Path(settings.BASE_DIR) / 'data' / 'exports'
    os.makedirs(out_dir, exist_ok=True)
    
    fmt = job.export_format.lower()
    filename = f"sunscrap_{job.snapshot.report_type}_{job.job_id}.{fmt}"
    file_path = str(out_dir / filename)
    
    try:
        if fmt == ExportFormat.CSV.lower():
            size, chk = generate_csv(job.snapshot, file_path)
        elif fmt == ExportFormat.XLSX.lower():
            size, chk = generate_xlsx(job.snapshot, file_path)
        elif fmt == ExportFormat.PDF.lower():
            size, chk = generate_pdf(job.snapshot, file_path)
        else:
            size, chk = generate_csv(job.snapshot, file_path)
            
        job.file_path = file_path
        job.file_size_bytes = size
        job.checksum = chk
        job.status = JobStatus.READY
        job.progress_pct = 100
        job.completed_at = timezone.now()
        job.save()
        return True, "Export generated successfully."
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.save(update_fields=['status', 'error_message'])
        return False, str(e)
