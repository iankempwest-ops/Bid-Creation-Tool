# KW Bid Tool — Kemp West, Inc.

Internal bid creation and estimating web application.

## Setup

```bash
pip install -r requirements.txt
python3 create_template.py   # generates data/templates/Master Bid Template.xlsx
python3 run.py               # starts on http://localhost:5000
```

Requires LibreOffice for PDF generation:
```bash
sudo apt-get install libreoffice
```

## Usage

- **Admin screen** (`/leads`) — Intake leads, fill customer info, mark Ready for Estimate
- **Estimator screen** (`/estimator`) — Select crew package, hours, margin, add equipment, generate PDF

## Rates Configuration

Edit these files to update rates (no code change needed):

- `data/crew_rates.json` — Crew package hourly rates
- `data/equipment_rates.json` — Specialty equipment hourly rates

## Bid Template

Place `Master Bid Template.xlsx` in `data/templates/` or run `create_template.py` to regenerate it.

The app fills these cells in Sheet1:

| Cell | Content |
|------|---------|
| C6 | Customer Name |
| C7 | Contact Name |
| C8–C9 | Billing Address |
| C11 | Phone |
| C13 | Email |
| C15–C16 | Project Location |
| L6 | Date |
| C19+ | Project Specifications |
| C27 | Crew description |
| M27 | Crew lump sum |
| D33 | Tax location code |
| M35 | Tax amount |
| M34 | Subtotal (formula) |
| M36 | Total (formula) |
