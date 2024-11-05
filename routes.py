from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, Supplier, Trip, Project, ExpenseCategory, Expense, Organization, Role
from datetime import datetime
from sqlalchemy import func, case, or_
from utils import admin_required, same_organization_required
import requests

fuel_types = {
    'Gasoline': {'scope1': 2.31, 'scope3': 0.61, 'kwh': 9.7},
    'Diesel': {'scope1': 2.68, 'scope3': 0.63, 'kwh': 10.7},
    'Electricity': {'scope1': 0, 'scope3': 0.05, 'kwh': 1},
}

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    organizations = Organization.query.all()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        organization_id = request.form.get('organization')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        if organization_id == 'new':
            # Store data in session instead of URL parameters
            session['username'] = username
            session['email'] = email
            session['password'] = password
            return redirect(url_for('create_organization'))
        
        organization = Organization.query.get(organization_id)
        if not organization:
            flash('Invalid organization', 'danger')
            return redirect(url_for('register'))
        
        role = Role.query.filter_by(organization_id=organization.id, name='User').first()
        if not role:
            role = Role(name='User', organization_id=organization.id)
            db.session.add(role)
            db.session.commit()
        
        user = User(username=username, email=email, organization_id=organization.id, role_id=role.id,
                   is_admin=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful! Welcome to EcoExpenseTracker.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html', organizations=organizations)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create_organization', methods=['GET', 'POST'])
def create_organization():
    if current_user.is_authenticated:
        flash('You are already part of an organization.', 'danger')
        return redirect(url_for('index'))
        
    # Check if we have the required session data from register
    if not all([
        session.get('username'),
        session.get('email'),
        session.get('password')
    ]):
        flash('Please complete the registration process first.', 'danger')
        return redirect(url_for('register'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        regnr = request.form.get('regnr')

        if Organization.query.filter_by(name=name).first():
            flash('Organization name already exists', 'danger')
            return redirect(url_for('create_organization'))

        if Organization.query.filter_by(regnr=regnr).first():
            flash('Organization with this registration number already exists', 'danger')
            return redirect(url_for('create_organization'))

        try:
            organization = Organization(name=name, description=description)
            organization.regnr = regnr  # Use the validator
            db.session.add(organization)
            db.session.commit()

            # Create default admin role
            admin_role = Role(name='Admin', organization_id=organization.id)
            db.session.add(admin_role)
            db.session.commit()

            # Create user from session data
            username = session.get('username')
            email = session.get('email')
            password = session.get('password')


            # Create user from session data
            username = session.get('username')
            email = session.get('email')
            password = session.get('password')

            if username and email and password:
                user = User(
                    username=username,
                    email=email,
                    organization_id=organization.id,
                    role_id=admin_role.id,
                    is_admin=True
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()

                session.pop('username', None)
                session.pop('email', None)
                session.pop('password', None)

                login_user(user)

                flash('Organization created successfully! Welcome to EcoExpenseTracker.', 'success')
                return redirect(url_for('index'))

            flash('Error creating user', 'danger')
            return redirect(url_for('register'))

        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('create_organization'))

    return render_template('create_organization.html')

# Organization management routes
@app.route('/organizations')
@login_required
@admin_required
def organizations():
    organizations = Organization.query.all()
    return render_template('organizations.html', organizations=organizations)

@app.route('/manage_users/<int:org_id>')
@login_required
@admin_required
def manage_users(org_id):
    organization = Organization.query.get_or_404(org_id)
    users = User.query.filter_by(organization_id=org_id).all()
    roles = Role.query.filter_by(organization_id=org_id).all()
    stats = organization.get_statistics()
    return render_template('manage_users.html', organization=organization, users=users, roles=roles, stats=stats)

@app.route('/manage_roles/<int:org_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_organization_roles(org_id):
    organization = Organization.query.get_or_404(org_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            role = Role(name=name, organization_id=org_id)
            db.session.add(role)
            db.session.commit()
            flash('Role added successfully', 'success')
        return redirect(url_for('manage_organization_roles', org_id=org_id))
    
    roles = Role.query.filter_by(organization_id=org_id).all()
    return render_template('manage_roles.html', organization=organization, roles=roles)

@app.route('/update_user_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    role_id = request.form.get('role_id')
    
    if role_id:
        role = Role.query.get(role_id)
        if role and role.organization_id == user.organization_id:
            user.role_id = role.id
            db.session.commit()
            flash('User role updated successfully', 'success')
    
    return redirect(url_for('manage_users', org_id=user.organization_id))

# Main application routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    query = Expense.query.filter_by(user_id=current_user.id)
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        category = request.form.get('category')
        project = request.form.get('project')
        supplier = request.form.get('supplier')
        trip = request.form.get('trip')
        currency = request.form.get('currency')
        
        if start_date:
            query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d'))
        if category:
            query = query.filter(Expense.category_id == category)
        if project:
            query = query.filter(Expense.project_id == project)
        if supplier:
            query = query.filter(Expense.supplier_id == supplier)
        if trip:
            query = query.filter(Expense.trip_id == trip)
        if currency:
            query = query.filter(Expense.currency == currency)
    
    expenses = query.order_by(Expense.date.desc()).all()
    total_amount = sum(expense.nok_amount for expense in expenses)
    
    summary = {}
    if expenses:
        summary['avg_amount'] = total_amount / len(expenses)
        summary['date_range'] = {
            'start': expenses[-1].date,
            'end': expenses[0].date
        }
    
    categories = ExpenseCategory.query.all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    suppliers = Supplier.query.filter_by(organization_id=current_user.organization_id).all()
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    currencies = ['NOK', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD']
    
    return render_template('expenses.html',
                         expenses=expenses,
                         categories=categories,
                         projects=projects,
                         suppliers=suppliers,
                         trips=trips,
                         currencies=currencies,
                         total_amount=total_amount,
                         summary=summary)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        currency = request.form.get('currency')
        exchange_rate = float(request.form.get('exchange_rate'))
        nok_amount = round(amount * exchange_rate, 2)
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        description = request.form.get('description')
        category_id = request.form.get('category')
        
        # Get or create supplier
        supplier_name = request.form.get('supplier')
        supplier = Supplier.query.filter_by(name=supplier_name, organization_id=current_user.organization_id).first()
        if not supplier:
            supplier = Supplier(name=supplier_name, contact='', organization_id=current_user.organization_id)
            db.session.add(supplier)
            db.session.commit()
        
        # Optional fields
        trip_id = request.form.get('trip') or None
        project_id = request.form.get('project') or None
        
        # Car distance and fuel specific fields
        # kilometers = float(request.form.get('kilometers', 0))
        # fuel_type = request.form.get('fuel_type', '')
        # fuel_amount_liters = float(request.form.get('fuel_amount_liters', 0))
        # scope1_co2_emissions = float(request.form.get('scope1_co2_emissions', 0))
        # scope3_co2_emissions = float(request.form.get('scope3_co2_emissions', 0))
        # kwh = float(request.form.get('kwh', 0))

        category = ExpenseCategory.query.get(category_id)

        kilometers = 0.0
        fuel_type = ''
        fuel_amount_liters = 0.0
        scope1_co2_emissions = 0.0
        scope3_co2_emissions = 0.0
        kwh = 0.0

        # Calculate emissions
        if category and category.name == 'Car - distance-based allowance':
            kilometers = float(request.form.get('kilometers', '0') or '0')
            fuel_type = request.form.get('fuel_type_dist', '')
            fuel_amount_liters = float(request.form.get('car_fuel_consumption', '0') or '0')

            if fuel_type in fuel_types:
                total_fuel_consumption = (fuel_amount_liters * kilometers) / 100
                scope1_co2_emissions = total_fuel_consumption * fuel_types[fuel_type]["scope1"]
                scope3_co2_emissions = total_fuel_consumption * fuel_types[fuel_type]["scope3"]
                kwh = total_fuel_consumption * fuel_types[fuel_type]["kwh"]
        elif category and category.name == 'Fuel Expenses':
            fuel_type = request.form.get('fuel_type', '')
            fuel_amount_liters = float(request.form.get('fuel_amount', '0') or '0')

            if fuel_type in fuel_types:
                scope1_co2_emissions = fuel_amount_liters * fuel_types[fuel_type]["scope1"]
                scope3_co2_emissions = fuel_amount_liters * fuel_types[fuel_type]["scope3"]
                kwh = fuel_amount_liters * fuel_types[fuel_type]["kwh"]
        
        expense = Expense(
            amount=amount,
            currency=currency,
            exchange_rate=exchange_rate,
            nok_amount=nok_amount,
            date=date,
            description=description,
            supplier_id=supplier.id,
            category_id=category_id,
            user_id=current_user.id,
            trip_id=trip_id,
            project_id=project_id,
            kilometers=kilometers,
            fuel_type=fuel_type,
            fuel_amount_liters=fuel_amount_liters,
            scope1_co2_emissions=scope1_co2_emissions,
            scope3_co2_emissions=scope3_co2_emissions,
            kwh=round(kwh, 2),
            # organization_id=current_user.organization_id
        )
        
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))
    
    categories = ExpenseCategory.query.all()
    suppliers = Supplier.query.filter_by(organization_id=current_user.organization_id).all()
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    currencies = ['NOK', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD']
    
    return render_template('add_expense.html',
                         categories=categories,
                         suppliers=suppliers,
                         trips=trips,
                         projects=projects,
                         currencies=currencies,
                         fuel_types=fuel_types)

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        flash('You can only delete your own expenses.', 'danger')
        return redirect(url_for('expenses'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        
        supplier = Supplier(name=name, contact=contact, organization_id=current_user.organization_id)
        db.session.add(supplier)
        db.session.commit()
        
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))
    
    suppliers = Supplier.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/trips', methods=['GET', 'POST'])
@login_required
def trips():
    if request.method == 'POST':
        name = request.form.get('name')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        
        trip = Trip(name=name, start_date=start_date, end_date=end_date, user_id=current_user.id)
        db.session.add(trip)
        db.session.commit()
        
        flash('Trip added successfully!', 'success')
        return redirect(url_for('trips'))
    
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    return render_template('trips.html', trips=trips)

@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        project = Project(name=name, description=description, user_id=current_user.id)
        db.session.add(project)
        db.session.commit()
        
        flash('Project added successfully!', 'success')
        return redirect(url_for('projects'))
    
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('projects.html', projects=projects)

@app.route('/settings')
@login_required
def settings():
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('settings.html', trips=trips, projects=projects)

@app.route('/expense_analysis')
@login_required
def expense_analysis():
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('expense_analysis.html', trips=trips, projects=projects)

# API routes for AJAX calls
@app.route('/api/search_suppliers')
@login_required
def search_suppliers():
    query = request.args.get('q', '').lower()
    suppliers = Supplier.query.filter(
        Supplier.organization_id == current_user.organization_id,
        Supplier.name.ilike(f'%{query}%')
    ).all()
    return jsonify([supplier.name for supplier in suppliers])

@app.route('/api/supplier_expenses')
@login_required
def supplier_expenses():
    trip_id = request.args.get('trip_id')
    project_id = request.args.get('project_id')
    
    query = db.session.query(
        Supplier.name,
        func.sum(Expense.nok_amount).label('total_amount')
    ).join(Expense).filter(
        Expense.user_id == current_user.id
    )
    
    if trip_id:
        query = query.filter(Expense.trip_id == trip_id)
    if project_id:
        query = query.filter(Expense.project_id == project_id)
    
    results = query.group_by(Supplier.name).all()
    
    return jsonify([{
        'name': name,
        'total_amount': float(total_amount)
    } for name, total_amount in results])

@app.route('/api/category_expenses')
@login_required
def category_expenses():
    trip_id = request.args.get('trip_id')
    project_id = request.args.get('project_id')
    
    query = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.nok_amount).label('total_amount')
    ).join(Expense).filter(
        Expense.user_id == current_user.id
    )
    
    if trip_id:
        query = query.filter(Expense.trip_id == trip_id)
    if project_id:
        query = query.filter(Expense.project_id == project_id)
    
    results = query.group_by(ExpenseCategory.name).all()
    
    return jsonify([{
        'name': name,
        'total_amount': float(total_amount)
    } for name, total_amount in results])

@app.route('/api/expense_summary')
@login_required
def expense_summary():
    trip_id = request.args.get('trip_id')
    project_id = request.args.get('project_id')
    
    query = Expense.query.filter_by(user_id=current_user.id)
    
    if trip_id:
        query = query.filter_by(trip_id=trip_id)
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    expenses = query.all()
    
    total_amount = sum(expense.nok_amount for expense in expenses)
    scope1_emissions = sum(expense.scope1_co2_emissions for expense in expenses)
    scope3_emissions = sum(expense.scope3_co2_emissions for expense in expenses)
    
    return jsonify({
        'total_amount': total_amount,
        'scope1_emissions': scope1_emissions,
        'scope3_emissions': scope3_emissions,
        'total_emissions': scope1_emissions + scope3_emissions
    })
