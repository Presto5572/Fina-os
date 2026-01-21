# clean_db.py is specifically for removing test data form the db.
from core.database import SheilaVault

vault = SheilaVault()

# The ID we used in the test was "acc_123"
print("🧹 Cleaning up dummy test data...")
vault.cursor.execute("DELETE FROM accounts WHERE account_id = 'acc_123'")
vault.conn.commit()

print("'My Secret Savings' (Dummy Data) has been removed.")
vault.close()