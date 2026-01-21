from core.database import SheilaVault
from core.plaid_client import SheilaConnector
import time

def sync_data(): # Think of this as the "Morning Snapshot" of all the records for you to use in the daily analysis.
    """
    The Routine:
    1. Wake up S.H.E.I.L.A. (Load DB and API Client)
    2. Check all accounts.
    3. Download latest transactions and holdings.
    4. Save to Memory.
    """
    print("S.H.E.I.L.A. | System Startup...")
    vault = SheilaVault()
    connector = SheilaConnector()

    # 1. Get all linked accounts
    accounts = vault.get_all_accounts()
    if not accounts:
        print("No accounts found. Run 'setup_server.py' first.")
        return

    print(f"S.H.E.I.L.A. | Found {len(accounts)} linked account(s). Starting sync...")

    for acc in accounts:
        account_id = acc[0]
        # Decrypt the name for display (acc[1] is name_encrypted)
        account_name = vault._decrypt(acc[1])
        # Decrypt the token for Plaid (acc[2] is access_token_encrypted)
        access_token = vault._decrypt(acc[2])

        print(f"\n   Syncing: {account_name}...")

        try:
            # --- STEP A: SYNC TRANSACTIONS (For Sentinel) ---
            transactions = connector.get_transactions(access_token)
            print(f"      Found {len(transactions)} recent transactions.")
            for t in transactions:
                vault.add_transaction(t)

            # --- STEP B: SYNC HOLDINGS (For Tax Scout) ---
            # Note: Investments endpoints only work on Investment accounts.
            # We wrap this in a try/except so checking accounts don't crash it.
            try:
                holdings, securities = connector.get_holdings(access_token)
                
                # Wipe old data for this account before adding new
                vault.clear_holdings(account_id)
                
                # Plaid separates 'Holdings' (Counts) from 'Securities' (Tickers).
                # We map them together here.
                sec_map = {s.security_id: s for s in securities}
                
                for h in holdings:
                    sec = sec_map.get(h.security_id)
                    ticker = sec.ticker_symbol if sec else "UNKNOWN"
                    price = sec.close_price if sec else 0.0
                    
                    vault.add_holding(
                        account_id=account_id,
                        ticker=ticker,
                        qty=h.quantity,
                        basis=h.cost_basis,
                        price=price,
                        currency=h.iso_currency_code
                    )
                print(f"      Saved {len(holdings)} investment positions.")
                
            except Exception as e:
                # If it's just a checking account, Plaid will complain about "Investments". Ignore it.
                if "PRODUCTS_NOT_SUPPORTED" in str(e):
                    print("      (Skipping Investments - Not an investment account)")
                else:
                    print(f"      Investment Sync Warning: {e}")

        except Exception as e:
            print(f"   Failed to sync {account_name}: {e}")

    print("\nS.H.E.I.L.A. | Sync Complete. Memory updated.")
    vault.close()

if __name__ == "__main__":
    sync_data()