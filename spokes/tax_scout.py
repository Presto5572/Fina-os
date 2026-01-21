from spokes.proxy_finder import get_proxy_suggestion

import yfinance as yf
from core.database import SheilaVault
import time

# CONFIGURATION
LOSS_THRESHOLD = -0.05  # We look for assets down 5% or more
MIN_HARVEST_AMOUNT = 1000  # Only bother if we can harvest $1,000+ in losses

def run_tax_scout():
    print("\n<<< TAX SCOUT HARVESTER >>>\n")
    print("---> Scanning portfolio for harvest opportunities...")
    vault = SheilaVault()
    
    # 1. Fetch all holdings from S.H.E.I.L.A.'s memory
    # Query the SQLite DB directly
    vault.cursor.execute("SELECT ticker, quantity, cost_basis, current_price FROM holdings")
    holdings = vault.cursor.fetchall()
    
    if not holdings:
        print("[X] Error: No holdings found. Please link a Brokerage account.")
        return

    print(f"\n---> Analyzing {len(holdings)} positions...")
    
    # 2. Group by Ticker (If one owns Stock A in two different accounts)
    portfolio = {}
    for h in holdings:
        ticker = h[0]
        qty = h[1]
        basis = h[2] # This is 'cost_basis_per_share' usually, or total. Plaid varies.
                     # Plaid 'cost_basis' is usually TOTAL cost. 
                     # Let's assume TOTAL for now, but valid checks are needed.
        
        if ticker not in portfolio:
            portfolio[ticker] = {'qty': 0, 'total_basis': 0}
        
        portfolio[ticker]['qty'] += qty
        portfolio[ticker]['total_basis'] += basis

# ... inside run_tax_scout() ...

    # 3. MAP & DOWNLOAD (The Fix)
    TICKER_MAP = {
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD',
        'LTC': 'LTC-USD'
    }

    raw_tickers = list(portfolio.keys())
    # Create a list of "Search Tickers" (e.g., replace BTC with BTC-USD)
    search_tickers = [TICKER_MAP.get(t, t) for t in raw_tickers if t and t != "UNKNOWN"]
    
    # Create a reverse map so we can turn 'BTC-USD' back into 'BTC' for the report
    reverse_map = {v: k for k, v in TICKER_MAP.items()}

    print(f"---> Fetching live prices for: {search_tickers}")
    
    if not search_tickers:
        print("[!] No valid tickers found to check.")
        return

    try:
        data_payload = yf.download(search_tickers + ['SPY'], period="1d", progress=False)
                
        # Handle the data structure
        if 'Close' in data_payload:
            current_data = data_payload['Close'].iloc[-1]
        else:
            current_data = data_payload.iloc[-1]
            
    except Exception as e:
        print(f"[X] Error: Market Data Incorrect {e}")
        return

    # 4. The Math (The "Alpha" Logic)
    harvest_opportunities = []
    
    print("---> Calculating performance...")

    for search_ticker in search_tickers:
        # Get the original portfolio ticker (e.g., BTC-USD -> BTC)
        original_ticker = reverse_map.get(search_ticker, search_ticker)
        
        if original_ticker not in portfolio: continue # Safety check

        position = portfolio[original_ticker]
        qty = position['qty']
        total_basis = position['total_basis']
        
        # Get live price safely using the SEARCH ticker
        try:
            # Check if we have data for this specific ticker
            if search_ticker not in current_data.index:
                # If it's a single item series (only 1 valid ticker found)
                if hasattr(current_data, 'name') and current_data.name == search_ticker:
                    live_price = current_data.item()
                else:
                    # Silent skip for ghosts
                    continue
            else:
                live_price = current_data[search_ticker]
                
            if str(live_price) == 'nan': continue

        except Exception as e:
            continue

        current_value = qty * live_price
        total_gain_loss = current_value - total_basis
        
        # Avoid division by zero
        pct_gain_loss = (total_gain_loss / total_basis) if total_basis > 0 else 0

        # 5. The Decision Matrix
        if pct_gain_loss <= LOSS_THRESHOLD: # Functional Threshold
            # Check threshold
            if total_gain_loss < -(MIN_HARVEST_AMOUNT / 10): 
                harvest_opportunities.append({
                    'ticker': original_ticker,
                    'loss_amount': total_gain_loss,
                    'pct_loss': pct_gain_loss * 100
                })
                print(f"   DETECTED: {original_ticker} is down {pct_gain_loss*100:.2f}% (Loss: ${total_gain_loss:.2f})")
            else:
                 print(f"   {original_ticker} is down, but only ${total_gain_loss:.2f}. Holding.")
        else:
            print(f"   {original_ticker} is healthy ({pct_gain_loss*100:.2f}%).")
        
        # TEST >>> 5. The Decision Matrix (Force Every Asset to be a Loss)
        # if True: # Force every asset to be treated as a "Loss"
        #     if True: # Force every asset to be "Big Enough" to harvest
        #         harvest_opportunities.append({
        #             'ticker': original_ticker,
        #             'loss_amount': total_gain_loss, # This might be positive, but that's fine for testing
        #             'pct_loss': pct_gain_loss * 100
        #         })
        #         print(f"   DETECTED (TEST): {original_ticker} sent to Harvest Queue.")
        #     else:
        #          print(f"   {original_ticker} is down, but only ${total_gain_loss:.2f}. Holding.")

 # 6. Report
    print("\n--- HARVEST REPORT ---\n")
    if harvest_opportunities:
        for opp in harvest_opportunities:
            ticker = opp['ticker']
            loss = abs(opp['loss_amount'])
            
            # CALL THE PROXY FINDER HERE
            proxy_advice = get_proxy_suggestion(ticker)
            
            print(f"RECOMMENDATION: Sell {ticker} to harvest ${loss:.2f} in losses.")
            print(f"   RECOVERY PLAN: Buy {proxy_advice}")
            print("-" * 40)
            
            vault.log_action("TAX_SCOUT", "HARVEST_ALERT", f"Found loss in {ticker}. Suggested: {proxy_advice}")
    else:
        print("All positions are currently stable or profitable. No harvest needed.")

    vault.close()

if __name__ == "__main__":
    run_tax_scout()
# ---> python3 -m spokes.tax_scout