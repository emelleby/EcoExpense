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
            return redirect(url_for('create_organization', username=username, email=email, password=password))
        
        organization = Organization.query.get(organization_id)
        if not organization:
            flash('Invalid organization', 'danger')
            return redirect(url_for('register'))
        
        role = Role.query.filter_by(organization_id=organization.id, name='User').first()
        if not role:
            role = Role(name='User', organization_id=organization.id)
            db.session.add(role)
            db.session.commit()
        
        user = User(username=username, email=email, organization_id=organization.id, role_id=role.id)
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

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/create_organization', methods=['GET', 'POST'])
def create_organization():
    # Add this check at the start of the function
    if current_user.is_authenticated:
        flash('You are already part of an organization.', 'danger')
        return redirect(url_for('index'))

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

                login_user(user)
                
                session.pop('username', None)
                session.pop('email', None)
                session.pop('password', None)
                
                flash('Organization created successfully! Welcome to EcoExpenseTracker.', 'success')
                return redirect(url_for('index'))
            
            flash('Error creating user', 'danger')
            return redirect(url_for('register'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('create_organization'))
    
    session['username'] = request.args.get('username')
    session['email'] = request.args.get('email')
    session['password'] = request.args.get('password')
    
    return render_template('create_organization.html')

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    categories = ExpenseCategory.query.all()
    suppliers = Supplier.query.filter_by(organization_id=current_user.organization_id).all()
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    currencies = ['NOK', 'USD', 'EUR', 'GBP']
    
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        currency = request.form.get('currency')
        exchange_rate = float(request.form.get('exchange_rate'))
        nok_amount = amount * exchange_rate
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        description = request.form.get('description')
        category_id = int(request.form.get('category'))
        supplier_name = request.form.get('supplier')
        trip_id = request.form.get('trip')
        project_id = request.form.get('project')
        
        # Handle fuel and car expenses
        kilometers = float(request.form.get('kilometers', 0))
        fuel_type = request.form.get('fuel_type', '')
        fuel_amount = float(request.form.get('fuel_amount', 0))
        
        # Calculate emissions based on fuel type
        scope1_emissions = 0
        scope3_emissions = 0
        kwh = 0
        
        if fuel_type in fuel_types:
            if kilometers > 0:  # Car distance-based expense
                fuel_consumption = float(request.form.get('car_fuel_consumption', 0))
                total_fuel = (fuel_consumption * kilometers) / 100
                scope1_emissions = total_fuel * fuel_types[fuel_type]['scope1']
                scope3_emissions = total_fuel * fuel_types[fuel_type]['scope3']
                kwh = total_fuel * fuel_types[fuel_type]['kwh']
            elif fuel_amount > 0:  # Fuel expense
                scope1_emissions = fuel_amount * fuel_types[fuel_type]['scope1']
                scope3_emissions = fuel_amount * fuel_types[fuel_type]['scope3']
                kwh = fuel_amount * fuel_types[fuel_type]['kwh']
        
        # Get or create supplier
        supplier = Supplier.query.filter_by(name=supplier_name, organization_id=current_user.organization_id).first()
        if not supplier:
            supplier = Supplier(name=supplier_name, contact='', organization_id=current_user.organization_id)
            db.session.add(supplier)
            db.session.commit()
        
        new_expense = Expense(
            amount=amount,
            currency=currency,
            exchange_rate=exchange_rate,
            nok_amount=nok_amount,
            date=date,
            description=description,
            supplier_id=supplier.id,
            category_id=category_id,
            user_id=current_user.id,
            trip_id=trip_id if trip_id else None,
            project_id=project_id if project_id else None,
            kilometers=kilometers,
            fuel_type=fuel_type,
            fuel_amount_liters=fuel_amount,
            scope1_co2_emissions=scope1_emissions,
            scope3_co2_emissions=scope3_emissions,
            kwh=kwh
        )
        
        db.session.add(new_expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('add_expense.html', 
                         categories=categories,
                         suppliers=suppliers,
                         trips=trips,
                         projects=projects,
                         currencies=currencies,
                         fuel_types=fuel_types)
