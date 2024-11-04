[Previous content preserved...]
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
        supplier = Supplier.query.filter_by(
            name=supplier_name,
            organization_id=current_user.organization_id
        ).first()
        if not supplier:
            supplier = Supplier(
                name=supplier_name,
                contact='',
                organization_id=current_user.organization_id
            )
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
[Rest of the file preserved...]
