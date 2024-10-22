from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, Supplier, Trip, Project, ExpenseCategory, Expense
from datetime import datetime
from sqlalchemy import func

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        supplier_id = request.form['supplier']
        amount = float(request.form['amount'])
        currency = request.form['currency']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        description = request.form['description']
        category_id = request.form['category']
        trip_id = request.form['trip'] if request.form['trip'] != '' else None
        project_id = request.form['project'] if request.form['project'] != '' else None

        new_expense = Expense(amount=amount, currency=currency, date=date, description=description,
                              supplier_id=supplier_id, category_id=category_id,
                              user_id=current_user.id, trip_id=trip_id, project_id=project_id)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses_list'))

    suppliers = Supplier.query.all()
    categories = ExpenseCategory.query.all()
    trips = Trip.query.all()
    projects = Project.query.all()
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD']
    return render_template('add_expense.html', suppliers=suppliers, categories=categories,
                           trips=trips, projects=projects, currencies=currencies)

@app.route('/expenses')
@login_required
def expenses_list():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('expenses_list.html', expenses=expenses)

@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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

@app.route('/expense_analysis')
@login_required
def expense_analysis():
    return render_template('expense_analysis.html')

@app.route('/api/supplier_expenses')
@login_required
def supplier_expenses():
    supplier_expenses = db.session.query(
        Supplier.name,
        func.sum(Expense.amount).label('total_amount')
    ).join(Expense).filter(Expense.user_id == current_user.id).group_by(Supplier.id).all()
    
    return jsonify([{'name': se.name, 'total_amount': float(se.total_amount)} for se in supplier_expenses])

@app.route('/api/category_expenses')
@login_required
def category_expenses():
    category_expenses = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.amount).label('total_amount')
    ).join(Expense).filter(Expense.user_id == current_user.id).group_by(ExpenseCategory.id).all()
    
    return jsonify([{'name': ce.name, 'total_amount': float(ce.total_amount)} for ce in category_expenses])

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
