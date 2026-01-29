from spokes.proxy_finder import get_proxy_suggestion

import yfinance as yf
from core.database import SheilaVault
import time
import re

# CONFIGURATION
LOSS_THRESHOLD = -.01  # We look for assets down 5% or more
MIN_HARVEST_AMOUNT = 0  # Only bother if we can harvest $1,000+ in losses

def run_tax_scout():
    print("\n<<< TAX SCOUT HARVESTER >>>\n")
    print("---> Scanning portfolio for harvest opportunities...")
    vault = SheilaVault()
    
    # 1. Fetch all holdings
    vault.cursor.execute("SELECT ticker, quantity, cost_basis, current_price FROM holdings")
    holdings = vault.cursor.fetchall()
    
    if not holdings:
        print("[X] Error: No holdings found. Please link a Brokerage account.")
        return

    # 2. Group by Ticker & Clean Data
    portfolio = {}
    print(f"\n---> Analyzing {len(holdings)} raw positions...")

    for h in holdings:
        # RAW DATA
        raw_ticker = h[0]
        qty = float(h[1])     
        raw_basis = float(h[2]) if h[2] else 0.0 
        
        # CLEANUP: Remove whitespace/newlines
        if not raw_ticker: continue
        ticker = raw_ticker.strip().upper() 
        
        # MATH FIX: Calculate Total Lot Cost
        # Assuming DB stores 'Cost Basis Per Share'
        total_lot_cost = raw_basis * qty 
        
        if ticker not in portfolio:
            portfolio[ticker] = {'qty': 0.0, 'total_basis': 0.0}
        
        portfolio[ticker]['qty'] += qty
        portfolio[ticker]['total_basis'] += total_lot_cost

    # 3. The Bouncer (Map & Filter)
    TICKER_MAP = {
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD',
        'LTC': 'LTC-USD'
    }

    raw_tickers = list(portfolio.keys())
    search_tickers = []
    reverse_map = {}

    print(f"---> Filtering {len(raw_tickers)} unique tickers...")
    
    for t in raw_tickers:
        if not t or t == "UNKNOWN": continue
        
        # Check Map first
        if t in TICKER_MAP:
            mapped = TICKER_MAP[t]
            search_tickers.append(mapped)
            reverse_map[mapped] = t
            continue

        # Filter Junk (Options/Internal IDs)
        if len(t) > 6 or re.search(r'\d{3,}', t):
            # Allow common exceptions if needed, otherwise skip
            print(f"     [Skip] Ignoring likely non-equity asset: {t}")
            continue
            
        search_tickers.append(t)
        reverse_map[t] = t

    print(f"---> Fetching prices for {len(search_tickers)} valid assets (checking last 5 days)...")
    
    if not search_tickers:
        print("[!] No valid tickers found to check.")
        return

    # 4. Download Market Data
    try:
        data_payload = yf.download(search_tickers + ['SPY'], period="5d", progress=False)
        
        if 'Close' in data_payload:
            price_history = data_payload['Close']
        else:
            price_history = data_payload
            
    except Exception as e:
        print(f"[X] Error: Market Data Incorrect {e}")
        return

    # 5. The Math (The "Alpha" Logic)
    harvest_opportunities = []
    print("---> Calculating performance...")

    for search_ticker in search_tickers:
        original_ticker = reverse_map.get(search_ticker, search_ticker)
        
        if original_ticker not in portfolio: continue 

        position = portfolio[original_ticker]
        qty = position['qty']
        total_basis = position['total_basis']
        
        # Get Price
        try:
            if search_ticker in price_history.columns:
                series = price_history[search_ticker]
            elif search_ticker in price_history.index: 
                 series = price_history
            else:
                print(f"     [?] No data returned for {original_ticker}")
                continue

            # Get last valid price (handles Mutual Funds)
            clean_series = series.dropna()
            if clean_series.empty:
                print(f"     [?] {original_ticker} returned empty data (Delisted?).")
                continue
            live_price = float(clean_series.iloc[-1])

        except Exception as e:
            print(f"     [!] Error calc for {original_ticker}: {e}")
            continue

        # Calculate Gain/Loss
        current_value = qty * live_price
        total_gain_loss = current_value - total_basis
        pct_gain_loss = (total_gain_loss / total_basis) if total_basis > 0 else 0

        # Decision Matrix
        if pct_gain_loss <= LOSS_THRESHOLD: 
            if total_gain_loss < -(MIN_HARVEST_AMOUNT / 10): # Scaled down for testing
                harvest_opportunities.append({
                    'ticker': original_ticker,
                    'loss_amount': total_gain_loss,
                    'pct_loss': pct_gain_loss * 100
                })
                print(f"   DETECTED: {original_ticker} is down {pct_gain_loss*100:.2f}% (Loss: ${total_gain_loss:.2f})")
            else:
                 print(f"   {original_ticker} is down, but only ${total_gain_loss:.2f}. Holding.")
        else:
            if pct_gain_loss >= 0:
                print(f"   {original_ticker} is healthy (+{pct_gain_loss*100:.2f}%).")
            else:
                print(f"   {original_ticker} is stable (Down {pct_gain_loss*100:.2f}% - No action needed).")

    # 6. Report
    print("\n--- HARVEST REPORT ---\n")
    if harvest_opportunities:
        for opp in harvest_opportunities:
            ticker = opp['ticker']
            loss = abs(opp['loss_amount'])
            
            # CALL THE PROXY FINDER
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