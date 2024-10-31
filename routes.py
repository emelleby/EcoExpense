from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, Supplier, Trip, Project, ExpenseCategory, Expense, Organization, Role
from datetime import datetime
from sqlalchemy import func, case
from utils import admin_required, same_organization_required
import re

fuel_types = {
    "Gasoline": {
        "scope1": 2.17, "scope3": 0.61, "kwh": 9.7
    }, 
    "Diesel": {
        "scope1": 2.54, "scope3": 0.62, "kwh": 10.7
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search("[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    return True, ""

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            organization_id = request.form['organization']

            # Validate input
            if not username or len(username) < 3:
                flash('Username must be at least 3 characters long', 'danger')
                return redirect(url_for('register'))

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash('Please enter a valid email address', 'danger')
                return redirect(url_for('register'))

            is_valid, msg = validate_password(password)
            if not is_valid:
                flash(msg, 'danger')
                return redirect(url_for('register'))

            # Check for existing username/email
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))

            # Handle new organization creation
            if organization_id == 'new':
                session['registration_data'] = {
                    'username': username,
                    'email': email,
                    'password': password
                }
                return redirect(url_for('create_organization'))

            # Create user with existing organization
            user = User(username=username, email=email, organization_id=organization_id)
            user.set_password(password)
            
            # Set default role
            default_role = Role.query.filter_by(organization_id=organization_id, name='User').first()
            if not default_role:
                default_role = Role(name='User', organization_id=organization_id)
                db.session.add(default_role)
                db.session.flush()
            
            user.role_id = default_role.id
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))

    organizations = Organization.query.all()
    return render_template('register.html', organizations=organizations)

@app.route('/create_organization', methods=['GET', 'POST'])
def create_organization():
    if 'registration_data' not in session:
        flash('Please fill in registration details first', 'danger')
        return redirect(url_for('register'))

    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']

            if not name or len(name) < 3:
                flash('Organization name must be at least 3 characters long', 'danger')
                return redirect(url_for('create_organization'))

            if Organization.query.filter_by(name=name).first():
                flash('Organization name already exists', 'danger')
                return redirect(url_for('create_organization'))

            # Create organization and roles
            org = Organization(name=name, description=description)
            db.session.add(org)
            db.session.flush()  # Get org.id without committing

            admin_role = Role(name='Admin', organization_id=org.id)
            user_role = Role(name='User', organization_id=org.id)
            db.session.add(admin_role)
            db.session.add(user_role)
            db.session.flush()

            # Create user from stored registration data
            reg_data = session['registration_data']
            user = User(
                username=reg_data['username'],
                email=reg_data['email'],
                organization_id=org.id,
                role_id=admin_role.id,
                is_admin=True
            )
            user.set_password(reg_data['password'])
            db.session.add(user)

            # Create default expense categories for the organization
            default_categories = [
                'Travel', 'Food', 'Accommodation', 'Office Supplies',
                'Car - distance-based allowance', 'Fuel Expenses'
            ]
            for category_name in default_categories:
                category = ExpenseCategory(name=category_name, organization_id=org.id)
                db.session.add(category)

            db.session.commit()
            session.pop('registration_data', None)

            flash('Organization created and registration completed! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Organization creation error: {str(e)}")
            flash('An error occurred while creating the organization. Please try again.', 'danger')
            return redirect(url_for('create_organization'))

    return render_template('create_organization.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/organizations')
@login_required
@admin_required
def organizations():
    organizations = Organization.query.filter_by(id=current_user.organization_id).all()
    return render_template('organizations.html', organizations=organizations)

@app.route('/manage_users/<int:org_id>')
@login_required
@admin_required
def manage_users(org_id):
    if org_id != current_user.organization_id:
        flash('You can only manage users in your own organization.', 'danger')
        return redirect(url_for('index'))

    organization = Organization.query.get_or_404(org_id)
    users = User.query.filter_by(organization_id=org_id).all()
    roles = Role.query.filter_by(organization_id=org_id).all()
    stats = organization.get_statistics()
    
    return render_template('manage_users.html', 
                         organization=organization,
                         users=users,
                         roles=roles,
                         stats=stats)

@app.route('/manage_organization_roles/<int:org_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_organization_roles(org_id):
    if org_id != current_user.organization_id:
        flash('You can only manage roles in your own organization.', 'danger')
        return redirect(url_for('index'))

    organization = Organization.query.get_or_404(org_id)
    
    if request.method == 'POST':
        name = request.form['name']
        if name:
            role = Role(name=name, organization_id=org_id)
            db.session.add(role)
            db.session.commit()
            flash('Role added successfully!', 'success')
            return redirect(url_for('manage_organization_roles', org_id=org_id))
    
    roles = Role.query.filter_by(organization_id=org_id).all()
    return render_template('manage_roles.html', organization=organization, roles=roles)

@app.route('/update_user_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.organization_id != current_user.organization_id:
        flash('You can only update roles for users in your organization.', 'danger')
        return redirect(url_for('index'))
    
    role_id = request.form.get('role_id')
    if role_id:
        role = Role.query.get_or_404(role_id)
        if role.organization_id != current_user.organization_id:
            flash('Invalid role selected.', 'danger')
        else:
            user.role_id = role_id
            db.session.commit()
            flash('User role updated successfully.', 'success')
    
    return redirect(url_for('manage_users', org_id=user.organization_id))

@app.route('/settings')
@login_required
def settings():
    try:
        trips = Trip.query.filter_by(user_id=current_user.id).all()
        projects = Project.query.filter_by(user_id=current_user.id).all()
        return render_template('settings.html', trips=trips, projects=projects)
    except Exception as e:
        app.logger.error(f"Settings error: {str(e)}")
        flash('Error loading settings. Please try again.', 'danger')
        return render_template('settings.html', trips=[], projects=[])

@app.route('/trips', methods=['GET', 'POST'])
@login_required
def trips():
    if request.method == 'POST':
        try:
            name = request.form['name']
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
            
            if start_date > end_date:
                flash('Start date cannot be after end date', 'danger')
                return redirect(url_for('settings'))
                
            new_trip = Trip(name=name, start_date=start_date, end_date=end_date, user_id=current_user.id)
            db.session.add(new_trip)
            db.session.commit()
            flash('Trip added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding trip. Please try again.', 'danger')
            app.logger.error(f"Trip creation error: {str(e)}")
        return redirect(url_for('settings'))

    trips = Trip.query.filter_by(user_id=current_user.id).all()
    return render_template('settings.html', trips=trips)

@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            new_project = Project(name=name, description=description, user_id=current_user.id)
            db.session.add(new_project)
            db.session.commit()
            flash('Project added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding project. Please try again.', 'danger')
            app.logger.error(f"Project creation error: {str(e)}")
        return redirect(url_for('settings'))

    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('settings.html', projects=projects)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        supplier_name = request.form['supplier'].strip()
        supplier = Supplier.query.filter(func.lower(Supplier.name) == func.lower(supplier_name)).first()

        if not supplier:
            supplier = Supplier(name=supplier_name, contact='', organization_id=current_user.organization_id)
            db.session.add(supplier)
            db.session.commit()

        amount = float(request.form['amount'])
        currency = request.form['currency']
        exchange_rate = float(request.form['exchange_rate'])
        nok_amount = amount * exchange_rate
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        description = request.form['description']
        category_id = int(request.form['category'])
        trip_id = request.form['trip'] if request.form['trip'] != '' else None
        project_id = request.form['project'] if request.form['project'] != '' else None

        category = ExpenseCategory.query.get(category_id)

        kilometers = 0.0
        fuel_type = ''
        fuel_amount_liters = 0.0
        scope1_co2_emissions = 0.0
        scope3_co2_emissions = 0.0
        kwh = 0.0

        if category and category.name == 'Car - distance-based allowance':
            kilometers = float(request.form.get('kilometers', '0') or '0')
            fuel_type = request.form.get('fuel_type_dist', '')
            fuel_amount_liters = float(request.form.get('fuel_amount_liters_dist', '0') or '0')

            if fuel_type in fuel_types:
                total_fuel_consumption = (fuel_amount_liters * kilometers) / 100
                scope1_co2_emissions = total_fuel_consumption * fuel_types[fuel_type]["scope1"]
                scope3_co2_emissions = total_fuel_consumption * fuel_types[fuel_type]["scope3"]
                kwh = total_fuel_consumption * fuel_types[fuel_type]["kwh"]
        elif category and category.name == 'Fuel Expenses':
            fuel_type = request.form.get('fuel_type', '')
            fuel_amount_liters = float(request.form.get('fuel_amount_liters', '0') or '0')

            if fuel_type in fuel_types:
                scope1_co2_emissions = fuel_amount_liters * fuel_types[fuel_type]["scope1"]
                scope3_co2_emissions = fuel_amount_liters * fuel_types[fuel_type]["scope3"]
                kwh = fuel_amount_liters * fuel_types[fuel_type]["kwh"]

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
            organization_id=current_user.organization_id,
            trip_id=trip_id,
            project_id=project_id,
            kilometers=kilometers,
            fuel_type=fuel_type,
            fuel_amount_liters=fuel_amount_liters,
            scope1_co2_emissions=scope1_co2_emissions,
            scope3_co2_emissions=scope3_co2_emissions,
            kwh=kwh
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully! <a href="/add_expense" class="btn btn-primary btn-sm ms-3">Add Another</a>', 'success')
        return redirect(url_for('expenses'))

    categories = ExpenseCategory.query.filter_by(organization_id=current_user.organization_id).all()
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    suppliers = Supplier.query.filter_by(organization_id=current_user.organization_id).all()
    currencies = ['NOK', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD']
    return render_template('add_expense.html', 
                         categories=categories,
                         trips=trips, 
                         projects=projects, 
                         suppliers=suppliers,
                         currencies=currencies,
                         fuel_types=fuel_types)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    query = Expense.query.filter_by(user_id=current_user.id, organization_id=current_user.organization_id)
    
    start_date = None
    end_date = None
    selected_category = None
    selected_project = None
    selected_supplier = None
    selected_trip = None
    selected_currency = None

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        selected_category = request.form.get('category')
        selected_project = request.form.get('project')
        selected_supplier = request.form.get('supplier')
        selected_trip = request.form.get('trip')
        selected_currency = request.form.get('currency')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Expense.date >= start_date)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Expense.date <= end_date)
        
        if selected_category:
            query = query.filter(Expense.category_id == selected_category)
        
        if selected_project:
            query = query.filter(Expense.project_id == selected_project)
        
        if selected_supplier:
            query = query.filter(Expense.supplier_id == selected_supplier)
        
        if selected_trip:
            query = query.filter(Expense.trip_id == selected_trip)
        
        if selected_currency:
            query = query.filter(Expense.currency == selected_currency)

    expenses = query.order_by(Expense.date.desc()).all()
    total_amount = sum(expense.nok_amount for expense in expenses)

    summary = {
        'total_amount': total_amount,
        'count': len(expenses)
    }

    if expenses:
        summary['avg_amount'] = total_amount / len(expenses)
        summary['date_range'] = {
            'start': min(expense.date for expense in expenses),
            'end': max(expense.date for expense in expenses)
        }

    categories = ExpenseCategory.query.filter_by(organization_id=current_user.organization_id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    suppliers = Supplier.query.filter_by(organization_id=current_user.organization_id).all()
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    currencies = ['NOK', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD']

    return render_template('expenses.html', 
                         expenses=expenses,
                         total_amount=total_amount,
                         summary=summary,
                         categories=categories,
                         projects=projects,
                         suppliers=suppliers,
                         trips=trips,
                         currencies=currencies,
                         start_date=start_date,
                         end_date=end_date,
                         selected_category=selected_category,
                         selected_project=selected_project,
                         selected_supplier=selected_supplier,
                         selected_trip=selected_trip,
                         selected_currency=selected_currency)

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id or expense.organization_id != current_user.organization_id:
        flash('You are not authorized to delete this expense.', 'danger')
        return redirect(url_for('expenses'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully.', 'success')
    return redirect(url_for('expenses'))

@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        new_supplier = Supplier(name=name, contact=contact, organization_id=current_user.organization_id)
        db.session.add(new_supplier)
        db.session.commit()
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))

    suppliers_list = Supplier.query.filter_by(organization_id=current_user.organization_id).all()
    return render_template('suppliers.html', suppliers=suppliers_list)

@app.route('/expense_analysis')
@login_required
def expense_analysis():
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('expense_analysis.html', trips=trips, projects=projects)

@app.route('/api/search_suppliers')
@login_required
def search_suppliers():
    query = request.args.get('q', '').lower()
    suppliers = Supplier.query.filter(
        func.lower(Supplier.name).contains(query),
        Supplier.organization_id == current_user.organization_id
    ).all()
    return jsonify([s.name for s in suppliers])

@app.route('/api/supplier_expenses')
@login_required
def supplier_expenses():
    query = db.session.query(
        Supplier.name,
        func.sum(Expense.nok_amount).label('total_amount')
    ).join(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.organization_id == current_user.organization_id
    )

    trip_id = request.args.get('trip_id')
    project_id = request.args.get('project_id')

    if trip_id:
        query = query.filter(Expense.trip_id == trip_id)
    if project_id:
        query = query.filter(Expense.project_id == project_id)

    supplier_expenses = query.group_by(Supplier.name).all()
    
    return jsonify([{'name': se.name, 'total_amount': float(se.total_amount)} for se in supplier_expenses])

@app.route('/api/category_expenses')
@login_required
def category_expenses():
    query = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.nok_amount).label('total_amount')
    ).join(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.organization_id == current_user.organization_id
    )

    trip_id = request.args.get('trip_id')
    project_id = request.args.get('project_id')

    if trip_id:
        query = query.filter(Expense.trip_id == trip_id)
    if project_id:
        query = query.filter(Expense.project_id == project_id)

    category_expenses = query.group_by(ExpenseCategory.name).all()
    
    return jsonify([{'name': ce.name, 'total_amount': float(ce.total_amount)} for ce in category_expenses])

@app.route('/api/expense_summary')
@login_required
def expense_summary():
    query = Expense.query.filter_by(
        user_id=current_user.id,
        organization_id=current_user.organization_id
    )
    
    trip_id = request.args.get('trip_id')
    project_id = request.args.get('project_id')
    
    if trip_id:
        query = query.filter(Expense.trip_id == trip_id)
    if project_id:
        query = query.filter(Expense.project_id == project_id)
        
    expenses = query.all()
    
    total_amount = sum(expense.nok_amount for expense in expenses)
    total_scope1 = sum(expense.scope1_co2_emissions for expense in expenses)
    total_scope3 = sum(expense.scope3_co2_emissions for expense in expenses)
    
    return jsonify({
        'total_amount': float(total_amount),
        'scope1_emissions': float(total_scope1),
        'scope3_emissions': float(total_scope3),
        'total_emissions': float(total_scope1 + total_scope3)
    })
