from app import db
from flask import current_app

def reset_migrations():
    # Connect to database and remove alembic_version table
    with current_app.app_context():
        db.engine.execute('DROP TABLE IF EXISTS alembic_version;')
        print("Dropped alembic_version table")

if __name__ == "__main__":
    reset_migrations()