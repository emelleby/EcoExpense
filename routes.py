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

@app.route('/api/search_suppliers')
@login_required
def search_suppliers():
    query = request.args.get('q', '').lower()
    suppliers = Supplier.query.filter(func.lower(Supplier.name).contains(query)).all()
    return jsonify([s.name for s in suppliers])

[... rest of the file remains unchanged ...]
