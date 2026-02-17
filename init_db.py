import sqlite3
import os

DB_PATH = "data/fina_os.db"

def initialize_database():
    print(f"🏗️  Initializing Database Schema at: {DB_PATH}")
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. TRANSACTIONS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        date TEXT,
        merchant TEXT,
        amount REAL,
        category TEXT,
        account_id TEXT
    )
    """)
    
    # 2. HOLDINGS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holdings (
        ticker TEXT,
        quantity REAL,
        cost_basis REAL,
        institution_price REAL,
        account_id TEXT,
        UNIQUE(ticker, account_id)
    )
    """)
    
    # 3. ACCOUNTS (Fixed: Added access_token and renamed id -> account_id)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT,
        subtype TEXT,
        mask TEXT,
        access_token TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database tables created successfully.")
    print("   - Table: transactions")
    print("   - Table: holdings")
    print("   - Table: accounts (with access_token)")

if __name__ == "__main__":
    initialize_database()