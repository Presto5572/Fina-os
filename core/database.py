""" This file handles the three things:
The Vault: Generates/Loads a secret key to lock your data.
The Schema: Creates the tables for Accounts, Holdings, and Transactions.
The Interaction: Provides Python methods for S.H.E.I.L.A. to save/read data.
"""

import sqlite3
import os
import json
from datetime import datetime
from cryptography.fernet import Fernet

# CONSTANTS
DB_PATH = 'data/fina_os.db'
KEY_PATH = 'config/secret.key'

class SheilaVault:
    """
    Handles the encryption and database interactions for Fina.os.
    Functions as the 'Memory' for S.H.E.I.L.A.
    """
    
    def __init__(self):
        self._ensure_paths()                     # 1. Ensure necessary folders exist
        self.cipher = self._load_or_create_key() # 2. Load or create encryption key
        # Allow multi-threaded access            # 3. Connect to the database
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False) 
        self.cursor = self.conn.cursor()         # 4. Initialize the database schema if it doesn't exist
        self._initialize_schema()                # 5. Create tables for accounts, holdings, transactions, and logs

    def _ensure_paths(self):
        """Creates necessary folders if they don't exist."""
        os.makedirs('data', exist_ok=True)
        os.makedirs('config', exist_ok=True)

    def _load_or_create_key(self):
        """
        Loads the encryption key. If one doesn't exist, it creates it.
        WARNING: If you lose 'secret.key', your encrypted data is unreadable.
        """
        if os.path.exists(KEY_PATH):
            with open(KEY_PATH, 'rb') as key_file:
                key = key_file.read()
        else:
            key = Fernet.generate_key()
            with open(KEY_PATH, 'wb') as key_file:
                key_file.write(key)
        return Fernet(key)

    def _encrypt(self, text):
        """Encrypts sensitive strings before storage."""
        if text is None: return None
        return self.cipher.encrypt(text.encode()).decode()

    def _decrypt(self, text):
        """Decrypts strings when reading back to Python."""
        if text is None: return None
        return self.cipher.decrypt(text.encode()).decode()

    def _initialize_schema(self):
        """Defines the memory structure for S.H.E.I.L.A."""
        
        # Table 1: Accounts (Linked Brokerages/Banks)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                name_encrypted TEXT,
                type TEXT,
                subtype TEXT,
                access_token_encrypted TEXT,
                last_synced TIMESTAMP
            )
        ''')

        # Table 2: Holdings (For Tax-Loss Scout)
        # Note: We store numbers as REAL/INTEGER because they aren't PII.
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                ticker TEXT,
                quantity REAL,
                cost_basis REAL,
                current_price REAL,
                currency TEXT,
                FOREIGN KEY(account_id) REFERENCES accounts(account_id)
            )
        ''')

        # Table 3: Transactions (For Sentinel & Simulator)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                account_id TEXT,
                merchant_name TEXT,
                amount REAL,
                date TEXT,
                category TEXT,
                is_potential_fraud BOOLEAN DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(account_id)
            )
        ''')
        
        # Table 4: Sheila's Log (Audit Trail)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                spoke_name TEXT,
                action TEXT,
                details TEXT
            )
        ''')

        self.conn.commit()
        print(f"S.H.E.I.L.A. Memory initialized at {DB_PATH}")

    # --- These are input methods (Writing to Memory) ---

    def add_account(self, account_id, name, type, subtype, access_token): # This is where encryption happens for the access token and name
        """Stores a new Plaid account with encryption."""
        sql = '''INSERT OR REPLACE INTO accounts 
                 (account_id, name_encrypted, type, subtype, access_token_encrypted, last_synced)
                 VALUES (?, ?, ?, ?, ?, ?)'''
        
        self.cursor.execute(sql, (
            account_id,
            self._encrypt(name),       # Encrypting Name
            type,
            subtype,
            self._encrypt(access_token), # Encrypting Token
            datetime.now()
        ))
        self.conn.commit() # Changes aren't saved to a db unil commit() them.

    def log_action(self, spoke, action, details):
        """Logs a system event for liability tracking."""
        self.cursor.execute('''
            INSERT INTO system_logs (timestamp, spoke_name, action, details)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now(), spoke, action, details))
        self.conn.commit()

    def get_all_accounts(self): # Returns a list of all linked accounts so we can loop through them
        self.cursor.execute("SELECT account_id, name_encrypted, access_token_encrypted FROM accounts")
        return self.cursor.fetchall()

    def add_transaction(self, t): # Saves a single transaction to memory.
        # Plaid categories are lists (e.g., ['Food', 'Restaurants']). We join them into a string.
        category = ", ".join(t.category) if t.category else "Uncategorized"
        
        sql = '''INSERT OR REPLACE INTO transactions 
                 (transaction_id, account_id, merchant_name, amount, date, category)
                 VALUES (?, ?, ?, ?, ?, ?)'''
        
        self.cursor.execute(sql, (
            t.transaction_id,
            t.account_id,
            t.name, # Merchant Name
            t.amount,
            t.date,
            category
        ))
        self.conn.commit()

    def add_holding(self, account_id, ticker, qty, basis, price, currency):
        """Saves a snapshot of an investment holding."""
        sql = '''INSERT INTO holdings 
                 (account_id, ticker, quantity, cost_basis, current_price, currency)
                 VALUES (?, ?, ?, ?, ?, ?)'''
        
        self.cursor.execute(sql, (
            account_id,
            ticker,
            qty,
            basis,
            price,
            currency
        ))
        self.conn.commit()

    def clear_holdings(self, account_id):
        """
        Holdings change daily. It's safer to wipe the old snapshot 
        and replace it with the new one to avoid duplicates.
        """
        self.cursor.execute("DELETE FROM holdings WHERE account_id = ?", (account_id,))
        self.conn.commit()

    # --- These are output methods (Reading from Memory) ---

    def get_account_token(self, account_id):
        """Retrieves and decrypts the access token for Plaid calls."""
        self.cursor.execute("SELECT access_token_encrypted FROM accounts WHERE account_id = ?", (account_id,))
        result = self.cursor.fetchone()
        if result:
            return self._decrypt(result[0])
        return None

    def close(self):
        self.conn.close()

# Quick Test to ensure it works
if __name__ == "__main__":
    vault = SheilaVault()
    # Mock data to test encryption
    vault.add_account("acc_123", "My Secret Savings", "depository", "savings", "access-sandbox-123")
    vault.log_action("CORE", "INIT", "Database created successfully.")
    print("Test Complete. Check 'data' folder.")