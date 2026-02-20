import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from app import db
from app.models import Lead, Estimate, EquipmentItem, BidFile
from app.services.tax import lookup_wa_tax
from app.services.pdf import generate_bid_pdf

estimator_bp = Blueprint('estimator', __name__, url_prefix='/estimator')


def _load_crew_rates():
    path = os.path.join(current_app.root_path, '..', 'data', 'crew_rates.json')
    with open(path) as f:
        return json.load(f)['packages']


def _load_equipment_rates():
    path = os.path.join(current_app.root_path, '..', 'data', 'equipment_rates.json')
    with open(path) as f:
        return json.load(f)['equipment']


@estimator_bp.route('/')
def leads_list():
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    from app.models import Customer
    query = db.session.query(Lead).join(Customer)

    if status_filter:
        query = query.filter(Lead.status == status_filter)
    else:
        query = query.filter(Lead.status.in_(Lead.ESTIMATOR_STATUSES))

    if search:
        query = query.filter(Customer.name.ilike(f'%{search}%'))

    leads = query.order_by(Lead.updated_at.desc()).all()
    statuses = Lead.ESTIMATOR_STATUSES

    return render_template('estimator/leads_list.html',
                           leads=leads,
                           statuses=statuses,
                           status_filter=status_filter,
                           search=search)


@estimator_bp.route('/lead/<int:lead_id>', methods=['GET', 'POST'])
def estimate(lead_id):
    lead = db.get_or_404(Lead, lead_id)
    customer = lead.customer
    crew_rates = _load_crew_rates()
    equipment_rates = _load_equipment_rates()

    est = lead.estimate

    if request.method == 'POST':
        action = request.form.get('action', 'save')

        crew_package_key = request.form.get('crew_package_key', '').strip()
        try:
            crew_hours = float(request.form.get('crew_hours', 0))
        except ValueError:
            crew_hours = 0.0
        try:
            margin_pct = float(request.form.get('margin_pct', 0))
        except ValueError:
            margin_pct = 0.0

        estimator_notes = request.form.get('estimator_notes', '').strip()

        # Equipment items from form
        equip_keys = request.form.getlist('equip_key[]')
        equip_hours = request.form.getlist('equip_hours[]')
        equip_rates_form = request.form.getlist('equip_rate[]')

        # Validate
        errors = []
        if not crew_package_key:
            errors.append('Select a crew package.')
        if crew_hours <= 0:
            errors.append('Crew hours must be greater than 0.')
        if margin_pct <= 0 or margin_pct >= 100:
            errors.append('Margin % must be between 0 and 100.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('estimator/estimate_form.html',
                                   lead=lead,
                                   customer=customer,
                                   estimate=est,
                                   crew_rates=crew_rates,
                                   equipment_rates=equipment_rates,
                                   form_data=request.form)

        # Calculate crew
        if crew_package_key in crew_rates:
            crew_rate = crew_rates[crew_package_key]['rate']
        else:
            crew_rate = 0.0

        crew_internal_cost = crew_hours * crew_rate
        margin_decimal = margin_pct / 100.0
        if margin_decimal < 1.0:
            crew_bid_amount = crew_internal_cost / (1.0 - margin_decimal)
        else:
            crew_bid_amount = crew_internal_cost

        # Calculate equipment
        equipment_total = 0.0
        equipment_data = []
        for i, key in enumerate(equip_keys):
            if not key:
                continue
            try:
                eh = float(equip_hours[i]) if i < len(equip_hours) else crew_hours
            except (ValueError, IndexError):
                eh = crew_hours
            if key in equipment_rates:
                er = equipment_rates[key]['rate']
            else:
                try:
                    er = float(equip_rates_form[i]) if i < len(equip_rates_form) else 0.0
                except (ValueError, IndexError):
                    er = 0.0
            et = eh * er
            equipment_total += et
            equipment_data.append({'key': key, 'hours': eh, 'rate': er, 'total': et})

        subtotal = crew_bid_amount + equipment_total

        # Tax lookup
        tax_code = ''
        tax_rate = 0.0
        tax_amount = 0.0
        total = subtotal

        if action in ('save', 'generate'):
            tax_result = lookup_wa_tax(
                lead.project_street,
                lead.project_city,
                lead.project_zip
            )
            if tax_result:
                tax_code = tax_result.get('code', '')
                tax_rate = tax_result.get('rate', 0.0)
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount

        # Persist estimate
        if est is None:
            est = Estimate(lead_id=lead.id)
            db.session.add(est)

        est.crew_package_key = crew_package_key
        est.crew_hours = crew_hours
        est.margin_pct = margin_pct
        est.crew_internal_cost = crew_internal_cost
        est.crew_bid_amount = crew_bid_amount
        est.equipment_total = equipment_total
        est.subtotal = subtotal
        est.tax_code = tax_code
        est.tax_rate = tax_rate
        est.tax_amount = tax_amount
        est.total = total
        est.estimator_notes = estimator_notes

        # Replace equipment items
        for item in list(est.equipment_items):
            db.session.delete(item)
        for ed in equipment_data:
            item = EquipmentItem(
                estimate=est,
                equipment_key=ed['key'],
                hours=ed['hours'],
                rate=ed['rate'],
                total=ed['total'],
            )
            db.session.add(item)

        db.session.flush()

        if action == 'generate':
            try:
                pdf_path = generate_bid_pdf(lead, est, crew_rates, equipment_rates)
                bid_file = BidFile(estimate_id=est.id, pdf_path=pdf_path)
                db.session.add(bid_file)
                lead.status = Lead.STATUS_GENERATED
                db.session.commit()
                flash('PDF generated successfully.', 'success')
                return redirect(url_for('estimator.estimate', lead_id=lead.id))
            except Exception as ex:
                db.session.rollback()
                flash(f'PDF generation failed: {ex}', 'error')
                return redirect(url_for('estimator.estimate', lead_id=lead.id))

        if action == 'status':
            new_status = request.form.get('new_status', lead.status)
            if new_status in Lead.ESTIMATOR_STATUSES:
                lead.status = new_status

        db.session.commit()
        flash('Estimate saved.', 'success')
        return redirect(url_for('estimator.estimate', lead_id=lead.id))

    return render_template('estimator/estimate_form.html',
                           lead=lead,
                           customer=customer,
                           estimate=est,
                           crew_rates=crew_rates,
                           equipment_rates=equipment_rates,
                           form_data={})


@estimator_bp.route('/download/<int:file_id>')
def download_pdf(file_id):
    bid_file = db.get_or_404(BidFile, file_id)
    pdf_path = bid_file.pdf_path
    if not os.path.exists(pdf_path):
        flash('PDF file not found on disk.', 'error')
        return redirect(url_for('estimator.estimate', lead_id=bid_file.estimate.lead_id))
    return send_file(pdf_path, as_attachment=True,
                     download_name=os.path.basename(pdf_path))
