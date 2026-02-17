import sqlite3
from datetime import datetime

class SheilaVault:
    def __init__(self, db_path="data/fina_os.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def add_account(self, account_id, name, type, subtype, mask, access_token):
        """Stores account metadata and the access token."""
        sql = """
        INSERT OR REPLACE INTO accounts 
        (account_id, name, type, subtype, mask, access_token)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(sql, (account_id, name, type, subtype, mask, access_token))
        self.conn.commit()

    def add_transaction(self, tx_id, date, merchant, amount, category, account_id):
        """Stores a single transaction."""
        sql = """
        INSERT OR IGNORE INTO transactions 
        (id, date, merchant, amount, category, account_id) 
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(sql, (tx_id, date, merchant, amount, category, account_id))
        self.conn.commit()

    def add_holding(self, ticker, quantity, cost_basis, price, account_id):
        """Stores investment holdings."""
        sql = """
        INSERT OR REPLACE INTO holdings 
        (ticker, quantity, cost_basis, institution_price, account_id) 
        VALUES (?, ?, ?, ?, ?)
        """
        self.cursor.execute(sql, (ticker, quantity, cost_basis, price, account_id))
        self.conn.commit()

    def get_holdings(self):
        self.cursor.execute("SELECT * FROM holdings")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()