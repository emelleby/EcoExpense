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
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('settings.html', trips=trips, projects=projects)

@app.route('/trips', methods=['GET', 'POST'])
@login_required
def trips():
    if request.method == 'POST':
        name = request.form['name']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        new_trip = Trip(name=name, start_date=start_date, end_date=end_date, user_id=current_user.id)
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
        new_project = Project(name=name, description=description, user_id=current_user.id)
        db.session.add(new_project)
        db.session.commit()
        flash('Project added successfully!', 'success')
        return redirect(url_for('settings'))

    return redirect(url_for('settings'))

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
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
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
        'count': len(expenses)
    }

    if expenses:
        summary['avg_amount'] = total_amount / len(expenses)
        summary['date_range'] = {
            'start': min(expense.date for expense in expenses),
            'end': max(expense.date for expense in expenses)
        }

    categories = ExpenseCategory.query.all()
    projects = Project.query.filter_by(user_id=current_user.id).all()
    suppliers = Supplier.query.all()
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

@app.route('/expense_analysis')
@login_required
def expense_analysis():
    return render_template('expense_analysis.html')

@app.route('/api/search_suppliers')
@login_required
def search_suppliers():
    query = request.args.get('q', '').lower()
    suppliers = Supplier.query.filter(func.lower(Supplier.name).contains(query)).all()
    return jsonify([s.name for s in suppliers])

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
