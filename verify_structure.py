from app import app, db
from sqlalchemy import text

with app.app_context():
    result = db.session.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'expense_category' 
        AND column_name = 'is_fuel';
    """))
    if result.fetchone():
        print("is_fuel column exists in expense_category table")
    else:
        print("is_fuel column does not exist")
