from datetime import datetime, timezone
from app import db


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    billing_street = db.Column(db.String(200))
    billing_city = db.Column(db.String(100))
    billing_state = db.Column(db.String(2))
    billing_zip = db.Column(db.String(10))
    primary_contact_name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    leads = db.relationship('Lead', back_populates='customer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'billing_street': self.billing_street,
            'billing_city': self.billing_city,
            'billing_state': self.billing_state,
            'billing_zip': self.billing_zip,
            'primary_contact_name': self.primary_contact_name,
            'phone': self.phone,
            'email': self.email,
        }

    @property
    def billing_address_full(self):
        parts = [self.billing_street]
        city_state_zip = ', '.join(filter(None, [
            self.billing_city,
            self.billing_state
        ]))
        if city_state_zip:
            parts.append(city_state_zip)
        if self.billing_zip:
            parts[-1] = parts[-1] + ' ' + self.billing_zip
        return '\n'.join(filter(None, parts))


class Lead(db.Model):
    __tablename__ = 'leads'

    STATUS_NEW = 'New Lead'
    STATUS_NEEDS_INFO = 'Needs Info'
    STATUS_READY = 'Ready for Estimate'
    STATUS_GENERATED = 'Bid Generated'
    STATUS_SENT = 'Sent'
    STATUS_WON = 'Won'
    STATUS_LOST = 'Lost'

    ADMIN_STATUSES = [STATUS_NEW, STATUS_NEEDS_INFO, STATUS_READY]
    ESTIMATOR_STATUSES = [STATUS_READY, STATUS_GENERATED, STATUS_SENT, STATUS_WON, STATUS_LOST]

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    project_street = db.Column(db.String(200))
    project_city = db.Column(db.String(100))
    project_state = db.Column(db.String(2))
    project_zip = db.Column(db.String(10))
    specs = db.Column(db.Text)
    date_received = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    status = db.Column(db.String(30), default=STATUS_NEW, index=True)
    created_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    customer = db.relationship('Customer', back_populates='leads')
    estimate = db.relationship('Estimate', back_populates='lead', uselist=False,
                               cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else '',
            'project_street': self.project_street,
            'project_city': self.project_city,
            'project_state': self.project_state,
            'project_zip': self.project_zip,
            'specs': self.specs,
            'date_received': self.date_received.isoformat() if self.date_received else '',
            'status': self.status,
            'created_by': self.created_by,
            'notes': self.notes,
        }

    @property
    def project_location_full(self):
        parts = [self.project_street]
        city_state = ', '.join(filter(None, [self.project_city, self.project_state]))
        if city_state:
            parts.append(city_state)
        if self.project_zip:
            if parts:
                parts[-1] = parts[-1] + ' ' + self.project_zip
            else:
                parts.append(self.project_zip)
        return '\n'.join(filter(None, parts))


class Estimate(db.Model):
    __tablename__ = 'estimates'

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False, unique=True)
    crew_package_key = db.Column(db.String(50))
    crew_hours = db.Column(db.Float)
    margin_pct = db.Column(db.Float)
    crew_internal_cost = db.Column(db.Float)
    crew_bid_amount = db.Column(db.Float)
    equipment_total = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float)
    tax_code = db.Column(db.String(20))
    tax_rate = db.Column(db.Float)
    tax_amount = db.Column(db.Float)
    total = db.Column(db.Float)
    estimator_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    lead = db.relationship('Lead', back_populates='estimate')
    equipment_items = db.relationship('EquipmentItem', back_populates='estimate',
                                       cascade='all, delete-orphan')
    files = db.relationship('BidFile', back_populates='estimate',
                             cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'crew_package_key': self.crew_package_key,
            'crew_hours': self.crew_hours,
            'margin_pct': self.margin_pct,
            'crew_internal_cost': self.crew_internal_cost,
            'crew_bid_amount': self.crew_bid_amount,
            'equipment_total': self.equipment_total,
            'subtotal': self.subtotal,
            'tax_code': self.tax_code,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'total': self.total,
            'estimator_notes': self.estimator_notes,
            'equipment_items': [ei.to_dict() for ei in self.equipment_items],
        }


class EquipmentItem(db.Model):
    __tablename__ = 'equipment_items'

    id = db.Column(db.Integer, primary_key=True)
    estimate_id = db.Column(db.Integer, db.ForeignKey('estimates.id'), nullable=False)
    equipment_key = db.Column(db.String(50))
    hours = db.Column(db.Float)
    rate = db.Column(db.Float)
    total = db.Column(db.Float)

    estimate = db.relationship('Estimate', back_populates='equipment_items')

    def to_dict(self):
        return {
            'id': self.id,
            'estimate_id': self.estimate_id,
            'equipment_key': self.equipment_key,
            'hours': self.hours,
            'rate': self.rate,
            'total': self.total,
        }


class BidFile(db.Model):
    __tablename__ = 'bid_files'

    id = db.Column(db.Integer, primary_key=True)
    estimate_id = db.Column(db.Integer, db.ForeignKey('estimates.id'), nullable=False)
    pdf_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    estimate = db.relationship('Estimate', back_populates='files')
