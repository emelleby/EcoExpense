from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import User, Supplier, Trip, Project, ExpenseCategory, Expense, Organization, Role
from datetime import datetime
from sqlalchemy import func, case
from utils import admin_required, same_organization_required

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
