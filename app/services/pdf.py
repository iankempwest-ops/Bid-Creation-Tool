"""
PDF generation service.
Process:
  1. Copy master Excel template
  2. Fill in all bid data using openpyxl
  3. Convert to PDF via LibreOffice headless
"""
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import numbers
from flask import current_app


def _currency(wb_cell, value):
    """Write a numeric currency value to an Excel cell with proper formatting."""
    wb_cell.value = float(value) if value is not None else 0.0
    wb_cell.number_format = '$#,##0.00'


def _write_wrapped(ws, start_row, col, text: str, max_rows: int = 6):
    """Write multi-line text across stacked rows in the same column."""
    if not text:
        return
    lines = str(text).split('\n')
    for i, line in enumerate(lines[:max_rows]):
        ws.cell(row=start_row + i, column=col).value = line


def generate_bid_pdf(lead, estimate, crew_rates: dict, equipment_rates: dict) -> str:
    """
    Fill the master Excel template and export to PDF.
    Returns the path to the generated PDF file.
    """
    template_path = current_app.config['BID_TEMPLATE_PATH']
    pdf_dir = current_app.config['PDF_FOLDER']

    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f'Master Bid Template not found at: {template_path}\n'
            'Please place "Master Bid Template.xlsx" in the data/templates/ folder.'
        )

    os.makedirs(pdf_dir, exist_ok=True)

    # Build output filename
    safe_name = ''.join(c if c.isalnum() or c in '- _' else '_'
                        for c in lead.customer.name)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    xlsx_name = f'Bid_{safe_name}_{lead.id}_{timestamp}.xlsx'
    xlsx_path = os.path.join(pdf_dir, xlsx_name)

    # Copy template
    shutil.copy2(template_path, xlsx_path)

    wb = load_workbook(xlsx_path)
    ws = wb.active  # Sheet1

    customer = lead.customer

    # ── Header Fields ──────────────────────────────────────────────
    # C6: Customer Name
    ws['C6'] = customer.name

    # C7: Contact name / phone / email
    contact_parts = [customer.primary_contact_name or '']
    ws['C7'] = contact_parts[0]

    # C8+: Billing Address (wrapped across rows)
    billing_lines = [
        customer.billing_street or '',
        f'{customer.billing_city or ""}, {customer.billing_state or ""} {customer.billing_zip or ""}'.strip(', '),
    ]
    ws['C8'] = billing_lines[0]
    if len(billing_lines) > 1:
        ws['C9'] = billing_lines[1]

    # C11: Telephone
    ws['C11'] = customer.phone or ''

    # C13: Email
    ws['C13'] = customer.email or ''

    # C15+: Project Location
    project_lines = [
        lead.project_street or '',
        f'{lead.project_city or ""}, {lead.project_state or ""} {lead.project_zip or ""}'.strip(', '),
    ]
    ws['C15'] = project_lines[0]
    if len(project_lines) > 1:
        ws['C16'] = project_lines[1]

    # L6: Date
    if lead.date_received:
        ws['L6'] = lead.date_received.strftime('%-m/%-d/%Y')
    else:
        ws['L6'] = datetime.now().strftime('%-m/%-d/%Y')

    # ── Project Specifications ──────────────────────────────────────
    # C19+ (wrapped)
    if lead.specs:
        spec_lines = lead.specs.split('\n')
        for i, line in enumerate(spec_lines[:6]):
            ws.cell(row=19 + i, column=3).value = line

    # ── Clear quotation area ────────────────────────────────────────
    for row in range(27, 34):
        ws.cell(row=row, column=3).value = None   # C27:C33
        ws.cell(row=row, column=13).value = None  # M27:M33
    ws['M35'] = None
    ws['D33'] = None

    # ── Crew line item ──────────────────────────────────────────────
    crew_label = 'Tree Care Services'
    if estimate.crew_package_key and estimate.crew_package_key in crew_rates:
        crew_label = crew_rates[estimate.crew_package_key]['label']

    # Build description including equipment (no pricing shown)
    desc_parts = [crew_label]

    if estimate.equipment_items:
        equip_labels = []
        for item in estimate.equipment_items:
            if item.equipment_key in equipment_rates:
                equip_labels.append(equipment_rates[item.equipment_key]['label'])
            else:
                equip_labels.append(item.equipment_key)
        if equip_labels:
            desc_parts.append('Includes: ' + ', '.join(equip_labels))

    ws['C27'] = desc_parts[0]
    if len(desc_parts) > 1:
        ws['C28'] = desc_parts[1]

    # M27: Crew bid amount (crew + equipment lump sum — NOT separated)
    _currency(ws['M27'], estimate.crew_bid_amount + (estimate.equipment_total or 0))

    # ── Totals section ──────────────────────────────────────────────
    # D33: Tax location code
    ws['D33'] = estimate.tax_code or ''

    # M35: Tax amount (formula already exists for subtotal/total)
    _currency(ws['M35'], estimate.tax_amount or 0)

    wb.save(xlsx_path)
    wb.close()

    # ── Convert to PDF via LibreOffice ──────────────────────────────
    pdf_path = _convert_to_pdf(xlsx_path, pdf_dir)

    # Clean up temp xlsx
    try:
        os.remove(xlsx_path)
    except OSError:
        pass

    return pdf_path


def _convert_to_pdf(xlsx_path: str, output_dir: str) -> str:
    """
    Use LibreOffice headless to convert xlsx to PDF.
    Returns path to generated PDF.
    """
    try:
        result = subprocess.run(
            [
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                xlsx_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        raise RuntimeError(
            'LibreOffice is not installed. Cannot convert Excel to PDF.\n'
            'Install with: sudo apt-get install libreoffice'
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError('LibreOffice conversion timed out after 60 seconds.')

    if result.returncode != 0:
        raise RuntimeError(
            f'LibreOffice conversion failed (exit {result.returncode}):\n'
            f'{result.stderr}'
        )

    # LibreOffice names the PDF the same as the xlsx with .pdf extension
    base = os.path.splitext(os.path.basename(xlsx_path))[0]
    pdf_path = os.path.join(output_dir, base + '.pdf')

    if not os.path.exists(pdf_path):
        raise RuntimeError(
            f'LibreOffice reported success but PDF not found at: {pdf_path}'
        )

    return pdf_path
