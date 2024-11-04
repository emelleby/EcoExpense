from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    regnr = db.Column(db.String(9), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', backref='organization', lazy='dynamic')

    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        
    # Validate the regnr field
    @validates('regnr')
    def validate_regnr(self, key, regnr):
        if not regnr.isdigit() or len(regnr) != 9:
            raise ValueError("Registration number must be exactly 9 digits")
        return regnr
        
    def get_statistics(self):
        total_users = self.users.count()
        total_expenses = sum(user.expenses.count() for user in self.users.all())
        total_amount = sum(
            expense.nok_amount 
            for user in self.users.all() 
            for expense in user.expenses.all()
        )
        return {
            'total_users': total_users,
            'total_expenses': total_expenses,
            'total_amount': total_amount
        }

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, name, organization_id):
        self.name = name
        self.organization_id = organization_id

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(255))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy='dynamic')
    trips = db.relationship('Trip', backref='user', lazy='dynamic')
    projects = db.relationship('Project', backref='user', lazy='dynamic')
    is_admin = db.Column(db.Boolean, default=False)

    @validates('organization_id', 'role_id')
    def validate_required_fields(self, key, value):
        if value is None:
            raise ValueError(f'{key} cannot be None')
        return value

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return self.role.name == role_name

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    expenses = db.relationship('Expense', backref='supplier', lazy=True)

    def __init__(self, name, contact, organization_id):
        self.name = name
        self.contact = contact
        self.organization_id = organization_id

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expenses = db.relationship('Expense', backref='trip', lazy=True)

    def __init__(self, name, start_date, end_date, user_id):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.user_id = user_id

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expenses = db.relationship('Expense', backref='project', lazy=True)

    def __init__(self, name, description, user_id):
        self.name = name
        self.description = description
        self.user_id = user_id

class ExpenseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    expenses = db.relationship('Expense', backref='category', lazy=True)

    def __init__(self, name):
        self.name = name

    __table_args__ = (
        db.UniqueConstraint('name', name='_name_uc'),
    )

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    exchange_rate = db.Column(db.Float, nullable=False, default=1.0)
    nok_amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kilometers = db.Column(db.Float, nullable=False, default=0.0)
    fuel_type = db.Column(db.String(50), nullable=False, default='')
    fuel_amount_liters = db.Column(db.Float, nullable=False, default=0.0)
    scope1_co2_emissions = db.Column(db.Float, nullable=False, default=0.0)
    scope3_co2_emissions = db.Column(db.Float, nullable=False, default=0.0)
    kwh = db.Column(db.Float, nullable=False, default=0.0)

    def __init__(self, amount, currency, exchange_rate, nok_amount, date, description, 
                 supplier_id, category_id, user_id, trip_id=None, project_id=None,
                 kilometers=0.0, fuel_type='', fuel_amount_liters=0.0,
                 scope1_co2_emissions=0.0, scope3_co2_emissions=0.0, kwh=0.0):
        self.amount = amount
        self.currency = currency
        self.exchange_rate = exchange_rate
        self.nok_amount = nok_amount
        self.date = date
        self.description = description
        self.supplier_id = supplier_id
        self.category_id = category_id
        self.user_id = user_id
        self.trip_id = trip_id
        self.project_id = project_id
        self.kilometers = kilometers
        self.fuel_type = fuel_type
        self.fuel_amount_liters = fuel_amount_liters
        self.scope1_co2_emissions = scope1_co2_emissions
        self.scope3_co2_emissions = scope3_co2_emissions
        self.kwh = kwh
