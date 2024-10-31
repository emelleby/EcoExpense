import os
import psycopg2

def check_db_state():
    database_url = os.environ['DATABASE_URL']

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    try:
        # List all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Tables in database:", [t[0] for t in tables])

        # Check supplier table specifically
        cur.execute("""
            SELECT 
                tc.constraint_name, 
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            LEFT JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_name = 'supplier'
        """)
        constraints = cur.fetchall()
        print("\nSupplier table constraints:", constraints)

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_db_state()