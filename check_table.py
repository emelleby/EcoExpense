import os
import psycopg2

def check_supplier_table():
    database_url = os.environ['DATABASE_URL']

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    try:
        # Get column info for supplier table
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'supplier';
        """)
        columns = cur.fetchall()
        print("Supplier table columns:")
        for col in columns:
            print(col)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_supplier_table()