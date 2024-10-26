from app import app, db
from models import ExpenseCategory

def update_category_name():
    with app.app_context():
        # Find the category
        category = ExpenseCategory.query.filter_by(name='car travel').first()
        if category:
            # Update the name
            category.name = 'Car - distance-based allowance'
            # Commit the change
            db.session.commit()
            print("Category name updated successfully")
        else:
            print("Category 'car travel' not found")

if __name__ == '__main__':
    update_category_name()
