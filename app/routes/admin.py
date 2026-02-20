from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Customer, Lead

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
def index():
    return redirect(url_for('admin.leads_list'))


@admin_bp.route('/leads')
def leads_list():
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    query = db.session.query(Lead).join(Customer)

    if status_filter:
        query = query.filter(Lead.status == status_filter)
    else:
        # Admin sees only admin-stage leads by default
        query = query.filter(Lead.status.in_(Lead.ADMIN_STATUSES))

    if search:
        query = query.filter(Customer.name.ilike(f'%{search}%'))

    leads = query.order_by(Lead.created_at.desc()).all()
    statuses = Lead.ADMIN_STATUSES

    return render_template('admin/leads_list.html',
                           leads=leads,
                           statuses=statuses,
                           status_filter=status_filter,
                           search=search)


@admin_bp.route('/leads/new', methods=['GET', 'POST'])
def new_lead():
    if request.method == 'POST':
        errors = []

        # Customer data
        customer_id = request.form.get('customer_id', '').strip()
        customer_name = request.form.get('customer_name', '').strip()
        contact_name = request.form.get('contact_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        billing_street = request.form.get('billing_street', '').strip()
        billing_city = request.form.get('billing_city', '').strip()
        billing_state = request.form.get('billing_state', '').strip().upper()
        billing_zip = request.form.get('billing_zip', '').strip()

        # Project data
        project_street = request.form.get('project_street', '').strip()
        project_city = request.form.get('project_city', '').strip()
        project_state = request.form.get('project_state', '').strip().upper()
        project_zip = request.form.get('project_zip', '').strip()
        specs = request.form.get('specs', '').strip()
        date_received_str = request.form.get('date_received', '')
        created_by = request.form.get('created_by', '').strip()
        update_customer = request.form.get('update_customer') == '1'

        # Validate customer name
        if len(customer_name) < 2:
            errors.append('Customer name must be at least 2 characters.')

        # Validate phone or email (at least one)
        if not phone and not email:
            errors.append('At least one of Phone or Email is required.')

        # Validate phone format
        digits = ''.join(c for c in phone if c.isdigit())
        if phone and len(digits) != 10:
            errors.append('Phone must contain exactly 10 digits.')

        # Validate email format
        if email and ('@' not in email or '.' not in email or len(email) < 5):
            errors.append('Email must be a valid address.')

        # Validate billing address
        if not billing_street:
            errors.append('Billing street address is required.')
        if not billing_city:
            errors.append('Billing city is required.')
        if len(billing_state) != 2:
            errors.append('Billing state must be 2 letters.')
        if len(billing_zip) != 5 or not billing_zip.isdigit():
            errors.append('Billing ZIP must be 5 digits.')

        # Validate project location
        if not project_street:
            errors.append('Project street address is required.')
        if not project_city:
            errors.append('Project city is required.')
        if len(project_state) != 2:
            errors.append('Project state must be 2 letters.')
        if len(project_zip) != 5 or not project_zip.isdigit():
            errors.append('Project ZIP must be 5 digits.')

        # Validate specs
        if len(specs) < 10:
            errors.append('Project specifications must be at least 10 characters.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('admin/lead_form.html',
                                   form_data=request.form,
                                   today=date.today().isoformat())

        # Format phone
        formatted_phone = f'({digits[0:3]}) {digits[3:6]}-{digits[6:10]}' if digits else ''

        # Parse date
        try:
            lead_date = date.fromisoformat(date_received_str) if date_received_str else date.today()
        except ValueError:
            lead_date = date.today()

        # Create or update customer
        if customer_id:
            customer = db.session.get(Customer, int(customer_id))
            if customer and update_customer:
                customer.name = customer_name
                customer.billing_street = billing_street
                customer.billing_city = billing_city
                customer.billing_state = billing_state
                customer.billing_zip = billing_zip
                customer.primary_contact_name = contact_name
                customer.phone = formatted_phone
                customer.email = email
        else:
            customer = Customer(
                name=customer_name,
                billing_street=billing_street,
                billing_city=billing_city,
                billing_state=billing_state,
                billing_zip=billing_zip,
                primary_contact_name=contact_name,
                phone=formatted_phone,
                email=email,
            )
            db.session.add(customer)

        db.session.flush()

        lead = Lead(
            customer_id=customer.id,
            project_street=project_street,
            project_city=project_city,
            project_state=project_state,
            project_zip=project_zip,
            specs=specs,
            date_received=lead_date,
            status=Lead.STATUS_NEW,
            created_by=created_by,
        )
        db.session.add(lead)
        db.session.commit()

        flash(f'Lead #{lead.id} created successfully.', 'success')
        return redirect(url_for('admin.edit_lead', lead_id=lead.id))

    return render_template('admin/lead_form.html',
                           form_data={},
                           today=date.today().isoformat())


@admin_bp.route('/leads/<int:lead_id>', methods=['GET', 'POST'])
def edit_lead(lead_id):
    lead = db.get_or_404(Lead, lead_id)
    customer = lead.customer

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        errors = []

        customer_name = request.form.get('customer_name', '').strip()
        contact_name = request.form.get('contact_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        billing_street = request.form.get('billing_street', '').strip()
        billing_city = request.form.get('billing_city', '').strip()
        billing_state = request.form.get('billing_state', '').strip().upper()
        billing_zip = request.form.get('billing_zip', '').strip()
        project_street = request.form.get('project_street', '').strip()
        project_city = request.form.get('project_city', '').strip()
        project_state = request.form.get('project_state', '').strip().upper()
        project_zip = request.form.get('project_zip', '').strip()
        specs = request.form.get('specs', '').strip()
        date_received_str = request.form.get('date_received', '')
        status = request.form.get('status', lead.status)
        notes = request.form.get('notes', '').strip()
        update_customer = request.form.get('update_customer') == '1'

        # Only allow admin statuses
        if status not in Lead.ADMIN_STATUSES:
            status = lead.status

        digits = ''.join(c for c in phone if c.isdigit())
        if not phone and not email:
            errors.append('At least one of Phone or Email is required.')
        if phone and len(digits) != 10:
            errors.append('Phone must contain exactly 10 digits.')
        if email and ('@' not in email or '.' not in email or len(email) < 5):
            errors.append('Email must be a valid address.')
        if not billing_street:
            errors.append('Billing street is required.')
        if not billing_city:
            errors.append('Billing city is required.')
        if len(billing_state) != 2:
            errors.append('Billing state must be 2 letters.')
        if len(billing_zip) != 5 or not billing_zip.isdigit():
            errors.append('Billing ZIP must be 5 digits.')
        if not project_street:
            errors.append('Project street is required.')
        if not project_city:
            errors.append('Project city is required.')
        if len(project_state) != 2:
            errors.append('Project state must be 2 letters.')
        if len(project_zip) != 5 or not project_zip.isdigit():
            errors.append('Project ZIP must be 5 digits.')
        if len(specs) < 10:
            errors.append('Project specifications must be at least 10 characters.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('admin/lead_form.html',
                                   lead=lead,
                                   form_data=request.form,
                                   today=date.today().isoformat())

        formatted_phone = f'({digits[0:3]}) {digits[3:6]}-{digits[6:10]}' if digits else ''

        if update_customer:
            customer.name = customer_name
            customer.billing_street = billing_street
            customer.billing_city = billing_city
            customer.billing_state = billing_state
            customer.billing_zip = billing_zip
            customer.primary_contact_name = contact_name
            customer.phone = formatted_phone
            customer.email = email

        lead.project_street = project_street
        lead.project_city = project_city
        lead.project_state = project_state
        lead.project_zip = project_zip
        lead.specs = specs
        lead.notes = notes
        lead.status = status
        try:
            lead.date_received = date.fromisoformat(date_received_str) if date_received_str else lead.date_received
        except ValueError:
            pass

        db.session.commit()

        if action == 'ready':
            lead.status = Lead.STATUS_READY
            db.session.commit()
            flash('Lead marked Ready for Estimate.', 'success')
            return redirect(url_for('admin.leads_list'))

        flash('Lead saved.', 'success')
        return redirect(url_for('admin.edit_lead', lead_id=lead.id))

    form_data = {
        'customer_name': customer.name,
        'contact_name': customer.primary_contact_name or '',
        'phone': customer.phone or '',
        'email': customer.email or '',
        'billing_street': customer.billing_street or '',
        'billing_city': customer.billing_city or '',
        'billing_state': customer.billing_state or '',
        'billing_zip': customer.billing_zip or '',
        'project_street': lead.project_street or '',
        'project_city': lead.project_city or '',
        'project_state': lead.project_state or '',
        'project_zip': lead.project_zip or '',
        'specs': lead.specs or '',
        'date_received': lead.date_received.isoformat() if lead.date_received else '',
        'notes': lead.notes or '',
        'status': lead.status,
    }

    return render_template('admin/lead_form.html',
                           lead=lead,
                           customer=customer,
                           form_data=form_data,
                           today=date.today().isoformat())
