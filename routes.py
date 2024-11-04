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

# Organization Management Routes
@app.route('/organizations')
@login_required
@admin_required
def organizations():
    organizations = Organization.query.all()
    return render_template('organizations.html', organizations=organizations)

@app.route('/manage_organization_roles/<int:org_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_organization_roles():
    organization = Organization.query.get_or_404(org_id)
    roles = Role.query.filter_by(organization_id=org_id).all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            role = Role(name=name, organization_id=org_id)
            db.session.add(role)
            db.session.commit()
            flash('Role added successfully!', 'success')
        return redirect(url_for('manage_organization_roles', org_id=org_id))
    
    return render_template('manage_roles.html', organization=organization, roles=roles)

# Expense Management Routes
@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    categories = ExpenseCategory.query.all()
    suppliers = Supplier.query.filter_by(organization_id=current_user.organization_id).all()
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    currencies = ['NOK', 'USD', 'EUR', 'GBP']
    
    query = Expense.query.filter_by(user_id=current_user.id)
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        if start_date:
            query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d'))
            
        end_date = request.form.get('end_date')
        if end_date:
            query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d'))
            
        category = request.form.get('category')
        if category:
            query = query.filter_by(category_id=category)
            
        project = request.form.get('project')
        if project:
            query = query.filter_by(project_id=project)
            
        supplier = request.form.get('supplier')
        if supplier:
            query = query.filter_by(supplier_id=supplier)
            
        trip = request.form.get('trip')
        if trip:
            query = query.filter_by(trip_id=trip)
            
        currency = request.form.get('currency')
        if currency:
            query = query.filter_by(currency=currency)
    
    expenses = query.order_by(Expense.date.desc()).all()
    total_amount = sum(expense.nok_amount for expense in expenses)
    
    summary = {
        'avg_amount': total_amount / len(expenses) if expenses else 0,
        'date_range': {
            'start': min(expense.date for expense in expenses) if expenses else None,
            'end': max(expense.date for expense in expenses) if expenses else None
        } if expenses else None
    }
    
    return render_template('expenses.html',
                         expenses=expenses,
                         categories=categories,
                         suppliers=suppliers,
                         trips=trips,
                         projects=projects,
                         currencies=currencies,
                         total_amount=total_amount,
                         summary=summary)

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

@app.route('/expense_report', methods=['GET', 'POST'])
@login_required
def expense_report():
    categories = ExpenseCategory.query.all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        category_id = request.form.get('category')
        project_id = request.form.get('project')
        
        query = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        expenses = query.order_by(Expense.date).all()
        total_amount = sum(expense.nok_amount for expense in expenses)
        
        return render_template('expense_report.html',
                             expenses=expenses,
                             categories=categories,
                             projects=projects,
                             start_date=start_date,
                             end_date=end_date,
                             total_amount=total_amount)
    
    return render_template('expense_report.html',
                         expenses=None,
                         categories=categories,
                         projects=projects)

# Resource Management Routes
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

# Analysis Routes
@app.route('/expense_analysis')
@login_required
def expense_analysis():
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('expense_analysis.html', trips=trips, projects=projects)

# Settings Route
@app.route('/settings')
@login_required
def settings():
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('settings.html', trips=trips, projects=projects)

# API Routes
@app.route('/api/search_suppliers')
@login_required
def search_suppliers():
    query = request.args.get('q', '').lower()
    suppliers = Supplier.query.filter(
        Supplier.organization_id == current_user.organization_id,
        Supplier.name.ilike(f'%{query}%')
    ).all()
    return jsonify([supplier.name for supplier in suppliers])

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
    ).group_by(Supplier.name)
    
    if trip_id:
        query = query.filter(Expense.trip_id == trip_id)
    if project_id:
        query = query.filter(Expense.project_id == project_id)
    
    results = query.all()
    return jsonify([{'name': name, 'total_amount': float(total)} for name, total in results])

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
    ).group_by(ExpenseCategory.name)
    
    if trip_id:
        query = query.filter(Expense.trip_id == trip_id)
    if project_id:
        query = query.filter(Expense.project_id == project_id)
    
    results = query.all()
    return jsonify([{'name': name, 'total_amount': float(total)} for name, total in results])
