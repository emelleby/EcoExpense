# inspect_db.py
from app import app, db
from sqlalchemy import inspect

def inspect_database():
    with app.app_context():
        inspector = inspect(db.engine)

        # Get all table names
        tables = inspector.get_table_names()

        print("\n=== DATABASE SCHEMA OVERVIEW ===\n")

        for table in tables:
            print(f"\n📋 Table: {table}")
            print("-" * (len(table) + 8))

            # Get columns for each table
            columns = inspector.get_columns(table)
            for column in columns:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                default = f"DEFAULT {column['default']}" if column['default'] else ""
                print(f"  - {column['name']}: {column['type']} {nullable} {default}")

            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table)
            if foreign_keys:
                print("\n  Foreign Keys:")
                for fk in foreign_keys:
                    print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

if __name__ == "__main__":
    inspect_database()