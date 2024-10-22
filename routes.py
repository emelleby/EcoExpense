from flask import render_template, request, redirect, url_for, flash
from app import app, db
from models import Supplier, Trip, Project, ExpenseCategory, Expense
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        supplier_id = request.form['supplier']
        amount = float(request.form['amount'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        description = request.form['description']
        category_id = request.form['category']
        trip_id = request.form['trip'] if request.form['trip'] != '' else None
        project_id = request.form['project'] if request.form['project'] != '' else None

        new_expense = Expense(amount=amount, date=date, description=description,
                              supplier_id=supplier_id, category_id=category_id,
                              trip_id=trip_id, project_id=project_id)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses_list'))

    suppliers = Supplier.query.all()
    categories = ExpenseCategory.query.all()
    trips = Trip.query.all()
    projects = Project.query.all()
    return render_template('add_expense.html', suppliers=suppliers, categories=categories,
                           trips=trips, projects=projects)

@app.route('/expenses')
def expenses_list():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expenses_list.html', expenses=expenses)

@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        new_supplier = Supplier(name=name, contact=contact)
        db.session.add(new_supplier)
        db.session.commit()
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))

    suppliers_list = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers_list)

@app.route('/trips', methods=['GET', 'POST'])
def trips():
    if request.method == 'POST':
        name = request.form['name']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        new_trip = Trip(name=name, start_date=start_date, end_date=end_date)
        db.session.add(new_trip)
        db.session.commit()
        flash('Trip added successfully!', 'success')
        return redirect(url_for('trips'))

    trips_list = Trip.query.all()
    return render_template('trips.html', trips=trips_list)

@app.route('/projects', methods=['GET', 'POST'])
def projects():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_project = Project(name=name, description=description)
        db.session.add(new_project)
        db.session.commit()
        flash('Project added successfully!', 'success')
        return redirect(url_for('projects'))

    projects_list = Project.query.all()
    return render_template('projects.html', projects=projects_list)

def create_default_categories():
    categories = ['Car Travel', 'Accommodation', 'Fuel Expenses', 'Food', 'Misc']
    for category_name in categories:
        if not ExpenseCategory.query.filter_by(name=category_name).first():
            new_category = ExpenseCategory(name=category_name)
            db.session.add(new_category)
    db.session.commit()

# This function will be called in app.py to create default categories
def init_app(app):
    with app.app_context():
        create_default_categories()
