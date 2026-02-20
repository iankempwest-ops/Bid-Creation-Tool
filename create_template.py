"""
create_template.py
Run this once to generate data/templates/Master Bid Template.xlsx
based on the column/row mapping in the spec.

Usage:
    python3 create_template.py
"""

import os
from openpyxl import Workbook
from openpyxl.styles import (
    Font, Alignment, PatternFill, Border, Side, numbers
)
from openpyxl.utils import get_column_letter

OUT_PATH = os.path.join(os.path.dirname(__file__),
                        'data', 'templates', 'Master Bid Template.xlsx')


def thin():
    return Side(border_style='thin', color='CCCCCC')


def make_border(top=False, bottom=False, left=False, right=False):
    return Border(
        top=Side(border_style='thin', color='CCCCCC') if top else Side(),
        bottom=Side(border_style='thin', color='CCCCCC') if bottom else Side(),
        left=Side(border_style='thin', color='CCCCCC') if left else Side(),
        right=Side(border_style='thin', color='CCCCCC') if right else Side(),
    )


GREEN  = '1B5E20'
LGREEN = 'E8F5E9'
GRAY   = 'F5F5F5'
DGRAY  = '616161'
WHITE  = 'FFFFFF'
BLACK  = '212121'


def h_font(size=11, bold=False, color=BLACK, italic=False):
    return Font(name='Calibri', size=size, bold=bold, color=color, italic=italic)


def h_fill(color):
    return PatternFill(fill_type='solid', fgColor=color)


def h_align(h='left', v='center', wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)


def build_template():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Sheet1'

    # ── Column widths ──────────────────────────────────────────
    col_widths = {
        'A': 2, 'B': 2, 'C': 30, 'D': 12, 'E': 10, 'F': 10,
        'G': 10, 'H': 10, 'I': 10, 'J': 10, 'K': 10, 'L': 12, 'M': 16,
    }
    for col, w in col_widths.items():
        ws.column_dimensions[col].width = w

    # ── Row heights ────────────────────────────────────────────
    for r in range(1, 40):
        ws.row_dimensions[r].height = 18
    for r in [1, 2, 3]:
        ws.row_dimensions[r].height = 24

    # ── Company header (rows 1-4) ──────────────────────────────
    ws.merge_cells('C1:M1')
    c = ws['C1']
    c.value = 'KEMP WEST, INC.'
    c.font = h_font(20, bold=True, color=GREEN)
    c.alignment = h_align('center', 'center')
    c.fill = h_fill(LGREEN)

    ws.merge_cells('C2:M2')
    c = ws['C2']
    c.value = 'Professional Tree Care & Utility Line Clearance'
    c.font = h_font(11, italic=True, color=DGRAY)
    c.alignment = h_align('center', 'center')

    ws.merge_cells('C3:M3')
    c = ws['C3']
    c.value = 'PROPOSAL / BID'
    c.font = h_font(14, bold=True, color=WHITE)
    c.alignment = h_align('center', 'center')
    c.fill = h_fill(GREEN)

    # ── Header label column (B) ────────────────────────────────
    labels = {
        6:  ('B6',  'Customer:'),
        7:  ('B7',  'Contact:'),
        8:  ('B8',  'Address:'),
        11: ('B11', 'Telephone:'),
        13: ('B13', 'Email:'),
        15: ('B15', 'Project:'),
        18: ('B18', 'Scope of Work:'),
    }
    for row, (addr, text) in labels.items():
        c = ws[addr]
        c.value = text
        c.font = h_font(10, bold=True, color=DGRAY)
        c.alignment = h_align('right', 'top')

    # Date label
    ws['K6'] = 'Date:'
    ws['K6'].font = h_font(10, bold=True, color=DGRAY)
    ws['K6'].alignment = h_align('right', 'center')

    # ── Data cells (merge C→J for wrapping text) ───────────────
    data_cells = {
        'C6': '', 'C7': '', 'C8': '', 'C11': '', 'C13': '', 'C15': '', 'L6': '',
    }
    for addr in data_cells:
        c = ws[addr]
        c.alignment = h_align('left', 'top', wrap=True)
        c.font = h_font(11)

    # Merge data columns
    for row in [6, 7, 11, 13]:
        ws.merge_cells(f'C{row}:J{row}')
    for row in [8, 9, 10]:
        ws.merge_cells(f'C{row}:J{row}')
    for row in [15, 16, 17]:
        ws.merge_cells(f'C{row}:J{row}')
    ws.merge_cells('L6:M6')

    # ── Specs area (rows 19-24) ────────────────────────────────
    ws.row_dimensions[18].height = 16
    ws['B19'] = 'Description:'
    ws['B19'].font = h_font(10, bold=True, color=DGRAY)
    ws['B19'].alignment = h_align('right', 'top')
    for row in range(19, 25):
        ws.merge_cells(f'C{row}:M{row}')
        ws.row_dimensions[row].height = 20
        c = ws.cell(row=row, column=3)
        c.alignment = h_align('left', 'top', wrap=True)
        c.font = h_font(11)

    # ── Quotation table header (row 25-26) ────────────────────
    ws.row_dimensions[25].height = 8  # spacer
    ws.row_dimensions[26].height = 22

    ws.merge_cells('C26:L26')
    c = ws['C26']
    c.value = 'Description'
    c.font = h_font(11, bold=True, color=WHITE)
    c.fill = h_fill(GREEN)
    c.alignment = h_align('center', 'center')
    c.border = make_border(top=True, bottom=True, left=True, right=True)

    c = ws['M26']
    c.value = 'Totals'
    c.font = h_font(11, bold=True, color=WHITE)
    c.fill = h_fill(GREEN)
    c.alignment = h_align('center', 'center')
    c.border = make_border(top=True, bottom=True, left=True, right=True)

    # ── Line item rows (27-32) ─────────────────────────────────
    for row in range(27, 33):
        ws.row_dimensions[row].height = 20
        ws.merge_cells(f'C{row}:L{row}')
        c = ws.cell(row=row, column=3)
        c.alignment = h_align('left', 'center', wrap=True)
        c.font = h_font(11)
        c.border = make_border(top=True, bottom=True, left=True)
        c.fill = h_fill(WHITE) if row % 2 == 0 else h_fill(GRAY)

        m = ws.cell(row=row, column=13)
        m.number_format = '$#,##0.00'
        m.alignment = h_align('right', 'center')
        m.font = h_font(11)
        m.border = make_border(top=True, bottom=True, left=True, right=True)
        m.fill = h_fill(WHITE) if row % 2 == 0 else h_fill(GRAY)

    # ── Tax code row (33) ─────────────────────────────────────
    ws.row_dimensions[33].height = 18
    ws['C33'] = 'WA Tax Location Code:'
    ws['C33'].font = h_font(10, italic=True, color=DGRAY)
    ws['C33'].alignment = h_align('right', 'center')
    ws.merge_cells('C33:C33')

    ws['D33'].alignment = h_align('left', 'center')
    ws['D33'].font = h_font(10, bold=True)

    # ── Totals section (34-36) ─────────────────────────────────
    ws.row_dimensions[34].height = 20
    ws.row_dimensions[35].height = 20
    ws.row_dimensions[36].height = 24

    total_labels = {34: 'Subtotal', 35: 'Sales Tax', 36: 'TOTAL'}
    for row, label in total_labels.items():
        ws.merge_cells(f'C{row}:L{row}')
        c = ws.cell(row=row, column=3)
        c.value = label
        c.font = h_font(11, bold=(row == 36), color=WHITE if row == 36 else BLACK)
        c.alignment = h_align('right', 'center')
        c.fill = h_fill(GREEN if row == 36 else LGREEN)
        c.border = make_border(top=True, bottom=True, left=True)

        m = ws.cell(row=row, column=13)
        m.number_format = '$#,##0.00'
        m.alignment = h_align('right', 'center')
        m.font = h_font(11, bold=(row == 36), color=WHITE if row == 36 else BLACK)
        m.fill = h_fill(GREEN if row == 36 else LGREEN)
        m.border = make_border(top=True, bottom=True, left=True, right=True)

    # Subtotal formula (sum of M27:M33)
    ws['M34'] = '=SUM(M27:M33)'

    # Total formula (subtotal + tax)
    ws['M36'] = '=M34+M35'

    # ── Footer ─────────────────────────────────────────────────
    ws.row_dimensions[38].height = 14
    ws.merge_cells('C38:M38')
    c = ws['C38']
    c.value = 'Thank you for the opportunity to provide this proposal. Prices valid for 30 days.'
    c.font = h_font(9, italic=True, color=DGRAY)
    c.alignment = h_align('center', 'center')

    # ── Print / page setup ─────────────────────────────────────
    ws.page_setup.orientation = 'portrait'
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_area = 'A1:M40'

    # ── Sheet protection (protect formulas, not data cells) ────
    # (not locking — estimator needs to write values)

    wb.save(OUT_PATH)
    print(f'Template created: {OUT_PATH}')


if __name__ == '__main__':
    build_template()
