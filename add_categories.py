from app import app, db
from models import ExpenseCategory

with app.app_context():
    # Add Fuel Expenses category if it doesn't exist
    fuel_category = ExpenseCategory.query.filter_by(name='Fuel Expenses').first()
    if not fuel_category:
        fuel_category = ExpenseCategory(name='Fuel Expenses', is_fuel=True)
        db.session.add(fuel_category)
        db.session.commit()
        print("Added 'Fuel Expenses' category")
    else:
        print("'Fuel Expenses' category already exists")

    # Add Car - Distance-based allowance category if it doesn't exist
    distance_category = ExpenseCategory.query.filter_by(name='Car - Distance-based allowance').first()
    if not distance_category:
        distance_category = ExpenseCategory(name='Car - Distance-based allowance', is_fuel=False)
        db.session.add(distance_category)
        db.session.commit()
        print("Added 'Car - Distance-based allowance' category")
    else:
        print("'Car - Distance-based allowance' category already exists")
