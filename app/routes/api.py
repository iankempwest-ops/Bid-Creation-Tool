from flask import Blueprint, request, jsonify
from app import db
from app.models import Customer, Lead

api_bp = Blueprint('api', __name__)


@api_bp.route('/customers/search')
def search_customers():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    customers = Customer.query.filter(
        Customer.name.ilike(f'%{q}%')
    ).order_by(Customer.name).limit(10).all()
    return jsonify([c.to_dict() for c in customers])


@api_bp.route('/customers/<int:customer_id>')
def get_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    return jsonify(customer.to_dict())


@api_bp.route('/leads/<int:lead_id>/status', methods=['POST'])
def update_lead_status(lead_id):
    lead = db.get_or_404(Lead, lead_id)
    data = request.get_json()
    new_status = data.get('status', '')
    allowed = Lead.ADMIN_STATUSES + [s for s in Lead.ESTIMATOR_STATUSES if s not in Lead.ADMIN_STATUSES]
    if new_status in allowed:
        lead.status = new_status
        db.session.commit()
        return jsonify({'ok': True, 'status': lead.status})
    return jsonify({'ok': False, 'error': 'Invalid status'}), 400
