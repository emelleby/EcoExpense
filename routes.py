from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, Supplier, Trip, Project, ExpenseCategory, Expense, Organization, Role
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
        organization_id = request.form.get('organization')
        
        if not organization_id:
            flash('Please select an organization', 'danger')
            return redirect(url_for('register'))
        
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
        
        # Check if this is the first user for the organization
        existing_users = User.query.filter_by(organization_id=organization_id).first()
        is_first_user = existing_users is None
        
        # Set default role based on whether this is the first user
        role_name = 'Admin' if is_first_user else 'Member'
        default_role = Role.query.filter_by(organization_id=organization_id, name=role_name).first()
        if not default_role:
            default_role = Role(name=role_name, organization_id=organization_id)
            db.session.add(default_role)
            db.session.commit()
        
        new_user = User(
            username=username, 
            email=email, 
            organization_id=organization_id, 
            role_id=default_role.id,
            is_admin=is_first_user  # Set admin status based on first user
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    
    organizations = Organization.query.all()
    return render_template('register.html', organizations=organizations)

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

@app.route('/organizations', methods=['GET', 'POST'])
@login_required
def organizations():
    if not current_user.is_admin:
        flash('Access denied. Only administrators can access this page.', 'danger')
        return redirect(url_for('index'))

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

@app.route('/organizations/<int:org_id>/roles', methods=['GET', 'POST'])
@login_required
def manage_organization_roles(org_id):
    if not current_user.is_admin:
        flash('Access denied. Only administrators can manage roles.', 'danger')
        return redirect(url_for('index'))

    organization = Organization.query.get_or_404(org_id)
    
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

# Rest of the routes remain unchanged...
