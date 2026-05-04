import sqlite3
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

DB_PATH = os.getenv("BHC_PROCESSED_DB_PATH")

def clear_database(db_path):
    if not db_path:
        print("❌ DB path not found in .env")
        return

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Connected to: {db_path}")

    cursor.execute("PRAGMA foreign_keys = OFF;")

    tables = cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%';
    """).fetchall()

    if not tables:
        print("No tables found.")
        return

    for (table_name,) in tables:
        print(f"Clearing table: {table_name}")
        cursor.execute(f"DELETE FROM {table_name};")

    conn.commit()

    print("Running VACUUM...")
    cursor.execute("VACUUM;")

    conn.close()
    print("✅ All data cleared successfully.")

if __name__ == "__main__":
    confirm = input("⚠️ This will delete ALL data. Continue? (y/n): ")
    if confirm.lower() == "y":
        clear_database(DB_PATH)
    else:
        print("Cancelled.")