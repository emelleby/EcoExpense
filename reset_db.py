# reset_db.py
# To run this
# rm -rf migrations/
# python reset_db.py
# Initialize new migrations folder
# flask db init

# Create initial migration
#flask db migrate -m "initial_migration"

# Apply the migration
#flask db upgrade


from app import app, db
from sqlalchemy import text  # Add this import at the top with other imports
from models import User, Organization, Role, Supplier, Trip, Project, ExpenseCategory, Expense

def init_categories():
    with app.app_context():
        categories = [
            'Car - distance-based allowance',
            'Fuel Expenses',
            'Flight',
            'Hotel',
            'Food',
            'Other'
        ]

        for category_name in categories:
            if not ExpenseCategory.query.filter_by(name=category_name).first():
                category = ExpenseCategory(name=category_name)
                db.session.add(category)

        db.session.commit()
        print("Expense categories initialized")

def reset_database():
    with app.app_context():
        try:
            # First, explicitly drop alembic_version table
            db.session.execute(text('DROP TABLE IF EXISTS alembic_version'))
            db.session.commit()
            print("Dropped alembic_version table")
            # Drop all tables
            db.drop_all()
            print("Dropped all tables")
            # Reset sequences
            sequences = [
                'user_id_seq', 'organization_id_seq', 'role_id_seq',
                'supplier_id_seq', 'trip_id_seq', 'project_id_seq',
                'expense_category_id_seq', 'expense_id_seq'
            ]

            for seq in sequences:
                try:
                    db.session.execute(text(f'ALTER SEQUENCE {seq} RESTART WITH 1'))
                    print(f"Reset sequence {seq}")
                except Exception as e:
                    print(f"Warning: Could not reset sequence {seq}: {str(e)}")
            # Recreate all tables
            db.create_all()
            init_categories()
            print("Recreated all tables.")
            db.session.commit()
            
            print("Database reset completed successfully")
        except Exception as e:
            print(f"Error resetting database: {str(e)}")
            db.session.rollback()
if __name__ == "__main__":
    reset_database()