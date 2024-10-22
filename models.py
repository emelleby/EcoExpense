from app import db
from datetime import datetime

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    expenses = db.relationship('Expense', backref='supplier', lazy=True)

    def __init__(self, name, contact):
        self.name = name
        self.contact = contact

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    expenses = db.relationship('Expense', backref='trip', lazy=True)

    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    expenses = db.relationship('Expense', backref='project', lazy=True)

    def __init__(self, name, description):
        self.name = name
        self.description = description

class ExpenseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    expenses = db.relationship('Expense', backref='category', lazy=True)

    def __init__(self, name):
        self.name = name

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)

    def __init__(self, amount, date, description, supplier_id, category_id, trip_id=None, project_id=None):
        self.amount = amount
        self.date = date
        self.description = description
        self.supplier_id = supplier_id
        self.category_id = category_id
        self.trip_id = trip_id
        self.project_id = project_id
