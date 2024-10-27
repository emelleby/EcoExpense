from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, Supplier, Trip, Project, ExpenseCategory, Expense, Organization, Role
from datetime import datetime
from sqlalchemy import func, case
from utils import admin_required, same_organization_required

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        organization_id = request.form.get('organization')
        
        if organization_id == "new":
            session['registration_data'] = {
                'username': username,
                'email': email,
                'password': password
            }
            return redirect(url_for('create_organization'))
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        organization = Organization.query.get(organization_id)
        if not organization:
            flash('Invalid organization selected', 'danger')
            return redirect(url_for('register'))
        
        default_role = Role.query.filter_by(organization_id=organization_id, name='Member').first()
        if not default_role:
            default_role = Role(name='Member', organization_id=organization_id)
            db.session.add(default_role)
            db.session.commit()
        
        new_user = User()
        new_user.username = username
        new_user.email = email
        new_user.organization_id = organization_id
        new_user.role_id = default_role.id
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    
    organizations = Organization.query.all()
    return render_template('register.html', organizations=organizations)

@app.route('/create_organization', methods=['GET', 'POST'])
def create_organization():
    if 'registration_data' not in session:
        flash('Please start registration first', 'danger')
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        if Organization.query.filter_by(name=name).first():
            flash('Organization name already exists', 'danger')
            return redirect(url_for('create_organization'))
        
        new_org = Organization(name=name, description=description)
        db.session.add(new_org)
        db.session.commit()
        
        admin_role = Role(name='Admin', organization_id=new_org.id)
        member_role = Role(name='Member', organization_id=new_org.id)
        db.session.add(admin_role)
        db.session.add(member_role)
        db.session.commit()
        
        reg_data = session.pop('registration_data')
        new_user = User()
        new_user.username = reg_data['username']
        new_user.email = reg_data['email']
        new_user.organization_id = new_org.id
        new_user.role_id = admin_role.id
        new_user.is_admin = True
        new_user.set_password(reg_data['password'])
        db.session.add(new_user)
        db.session.commit()
        
        flash('Organization created and you have been registered as admin. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('create_organization.html')

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

@app.route('/settings')
@login_required
def settings():
    # Get trips and projects for the current user's organization
    trips = Trip.query.join(Expense).join(User).filter(User.organization_id == current_user.organization_id).distinct().all()
    projects = Project.query.join(Expense).join(User).filter(User.organization_id == current_user.organization_id).distinct().all()
    return render_template('settings.html', trips=trips, projects=projects)

@app.route('/organizations', methods=['GET', 'POST'])
@login_required
@admin_required
def organizations():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        if Organization.query.filter_by(name=name).first():
            flash('Organization name already exists', 'danger')
            return redirect(url_for('organizations'))
        
        new_org = Organization(name=name, description=description)
        db.session.add(new_org)
        db.session.commit()
        
        default_roles = ['Admin', 'Member']
        for role_name in default_roles:
            role = Role(name=role_name, organization_id=new_org.id)
            db.session.add(role)
        db.session.commit()
        
        flash('Organization added successfully!', 'success')
        return redirect(url_for('organizations'))

    organizations = Organization.query.all()
    return render_template('organizations.html', organizations=organizations)

@app.route('/organizations/<int:org_id>/manage_users')
@login_required
@admin_required
def manage_users(org_id):
    organization = Organization.query.get_or_404(org_id)
    
    if organization.id != current_user.organization_id and not current_user.is_admin:
        flash('You can only manage users in your own organization.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.filter_by(organization_id=org_id).all()
    roles = Role.query.filter_by(organization_id=org_id).all()
    stats = organization.get_statistics()
    
    return render_template('manage_users.html', 
                         organization=organization,
                         users=users,
                         roles=roles,
                         stats=stats)

@app.route('/organizations/users/<int:user_id>/update_role', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role_id = request.form.get('role_id')
    
    if user.organization_id != current_user.organization_id and not current_user.is_admin:
        flash('You can only update roles for users in your organization.', 'danger')
        return redirect(url_for('index'))
    
    new_role = Role.query.get(new_role_id)
    if not new_role or new_role.organization_id != user.organization_id:
        flash('Invalid role selected.', 'danger')
        return redirect(url_for('manage_users', org_id=user.organization_id))
    
    user.role_id = new_role_id
    db.session.commit()
    flash('User role updated successfully.', 'success')
    return redirect(url_for('manage_users', org_id=user.organization_id))

@app.route('/organizations/<int:org_id>/roles', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_organization_roles(org_id):
    organization = Organization.query.get_or_404(org_id)
    
    if not current_user.is_admin:
        flash('Only administrators can manage roles', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        
        if Role.query.filter_by(organization_id=org_id, name=name).first():
            flash('Role already exists in this organization', 'danger')
            return redirect(url_for('manage_organization_roles', org_id=org_id))
        
        new_role = Role(name=name, organization_id=org_id)
        db.session.add(new_role)
        db.session.commit()
        
        flash('Role added successfully!', 'success')
        return redirect(url_for('manage_organization_roles', org_id=org_id))

    roles = Role.query.filter_by(organization_id=org_id).all()
    return render_template('manage_roles.html', organization=organization, roles=roles)

@app.route('/api/search_suppliers')
@login_required
def search_suppliers():
    query = request.args.get('q', '').lower()
    suppliers = Supplier.query.filter(func.lower(Supplier.name).contains(query)).all()
    return jsonify([s.name for s in suppliers])

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        supplier_name = request.form['supplier'].strip()
        supplier = Supplier.query.filter(func.lower(Supplier.name) == func.lower(supplier_name)).first()
        
        if not supplier:
            supplier = Supplier(name=supplier_name, contact='')
            db.session.add(supplier)
            db.session.commit()
        
        amount = float(request.form['amount'])
        currency = request.form['currency']
        exchange_rate = float(request.form['exchange_rate'])
        nok_amount = amount * exchange_rate
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        description = request.form['description']
        category_id = request.form['category']
        trip_id = request.form['trip'] if request.form['trip'] != '' else None
        project_id = request.form['project'] if request.form['project'] != '' else None

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
            trip_id=trip_id,
            project_id=project_id
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))

    categories = ExpenseCategory.query.all()
    trips = Trip.query.all()
    projects = Project.query.all()
    currencies = ['NOK', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD']
    return render_template('add_expense.html', categories=categories,
                         trips=trips, projects=projects, currencies=currencies)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    query = Expense.query.filter_by(user_id=current_user.id)
    
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
        'count': len(expenses),
    }

    if expenses:
        summary['avg_amount'] = total_amount / len(expenses)
        summary['date_range'] = {
            'start': min(expense.date for expense in expenses),
            'end': max(expense.date for expense in expenses)
        }

    categories = ExpenseCategory.query.all()
    projects = Project.query.all()
    suppliers = Supplier.query.all()
    trips = Trip.query.all()
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
    if expense.user_id != current_user.id:
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
        return redirect(url_for('settings'))

    return redirect(url_for('settings'))

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
        return redirect(url_for('settings'))

    return redirect(url_for('settings'))

@app.route('/expense_analysis')
@login_required
def expense_analysis():
    return render_template('expense_analysis.html')

@app.route('/api/supplier_expenses')
@login_required
def supplier_expenses():
    supplier_expenses = db.session.query(
        Supplier.name,
        func.sum(Expense.nok_amount).label('total_amount')
    ).join(Expense).filter(Expense.user_id == current_user.id).group_by(Supplier.name).all()
    
    return jsonify([{'name': se.name, 'total_amount': float(se.total_amount)} for se in supplier_expenses])

@app.route('/api/category_expenses')
@login_required
def category_expenses():
    category_expenses = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.nok_amount).label('total_amount')
    ).join(Expense).filter(Expense.user_id == current_user.id).group_by(ExpenseCategory.name).all()
    
    return jsonify([{'name': ce.name, 'total_amount': float(ce.total_amount)} for ce in category_expenses])
