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
