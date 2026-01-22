# Archived due to cost concerns with frequent OpenAI calls, lack of substantial data, and limited scope.

import yfinance as yf
import os
import openai
from dotenv import load_dotenv
from core.database import SheilaVault

load_dotenv()

# CONFIGURATION
VOLATILITY_THRESHOLD = 0.00 # 3% move triggers an explanation | To test use 0.00% -- Forces AI to explain every stock movement
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_market_news(ticker):
    """
    Fetches the top 3 headlines for a specific ticker using yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news
        
        # Extract just the titles and links to save tokens
        headlines = []
        if news_items:
            for item in news_items[:3]: # Top 3 only
                headlines.append(f"- {item['title']} ({item['publisher']})")
        
        return "\n".join(headlines)
    except Exception as e:
        return f"Error fetching news: {e}"

def generate_explanation(ticker, pct_change, headlines):
    """
    Asks S.H.E.I.L.A. to correlate the price move with the news.
    """
    direction = "UP" if pct_change > 0 else "DOWN"
    
    prompt = f"""
    <ROLE>
    You are S.H.E.I.L.A., a concise, friendly, non-professionally certified financial AI expert specializing in tax-loss harvesting strategies. You are only to recommend or suggest; never give official financial advice.
    
    <INPUT DATA>
    Asset: {ticker}
    Movement: {direction} {abs(pct_change)*100:.2f}% today.
    News Headlines:
    {headlines}
    
    <TASK>
    Summarize the most relevant headline in ONE sentence. 
    If the news explains the price movement, state the cause clearly.
    If the news seems generic or unrelated to today's move, just summarize the news anyway but add "(Correlation Unclear)."
    
    <TONE>
    Professional, direct, no fluff.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial news analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Analysis unavailable."

def run_narrator():
    print("\n<<< THE ALPHA NARRATOR >>>\n")
    print("---> Scanning portfolio for volatility...")
    
    vault = SheilaVault()
    vault.cursor.execute("SELECT ticker, quantity FROM holdings")
    holdings = vault.cursor.fetchall()
    
    # 1. Consolidate Portfolio (Get unique active tickers)
    # We filter out 'None' or empty tickers immediately
    active_tickers = list(set([h[0] for h in holdings if h[0]]))
    
    # Map crypto if needed (Reusing logic from Tax Scout)
    TICKER_MAP = {'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'LTC': 'LTC-USD'}
    
    search_tickers = [TICKER_MAP.get(t, t) for t in active_tickers if t != "UNKNOWN"]
    
    print(f"---> Checking {len(search_tickers)} assets for major moves (> {VOLATILITY_THRESHOLD*100}%)...")

    # 2. Bulk Download Prices (Efficiency)
    try:
        data = yf.download(search_tickers, period="1d", progress=False)['Close']
        # Calculate daily return: (Current - Open) / Open
        # Note: yf.download(period='1d') gives minute data usually, or just open/close.
        # Better approach for volatility: Get 2 days of history to compare Close vs Close
        data_hist = yf.download(search_tickers, period="5d", progress=False)['Close']
    except Exception as e:
        print(f"[X] Data Fetch Error: {e}")
        return

    # 3. Analyze Each Ticker
    for ticker in search_tickers:
        try:
            # Handle Single Ticker vs Multi-Ticker DataFrames
            if len(search_tickers) == 1:
                history = data_hist # It's already a Series
            else:
                if ticker not in data_hist: continue
                history = data_hist[ticker]
            
            # Drop NaNs and get last 2 days
            history = history.dropna()
            if len(history) < 2: continue
            
            prev_close = history.iloc[-2]
            current_price = history.iloc[-1]
            
            pct_change = (current_price - prev_close) / prev_close
            
            # 4. The Trigger
            if abs(pct_change) >= VOLATILITY_THRESHOLD:
                print(f"\n⚡ VOLATILITY DETECTED: {ticker} is {pct_change*100:.2f}%")
                
                # Fetch News
                print(f"   Reading the news for {ticker}...")
                headlines = get_market_news(ticker)

                # --- NEW DEBUG LINE ---
                print(f"   [DEBUG] Headlines Found:\n{headlines}") 
                # ----------------------
                
                if not headlines:
                    print(f"   (No recent news found for {ticker})")
                    continue
                    
                # Ask AI
                explanation = generate_explanation(ticker, pct_change, headlines)
                print(f"   S.H.E.I.L.A.: \"{explanation}\"")
                
                # Log it
                vault.log_action("NARRATOR", "EXPLAINED_MOVE", f"{ticker}: {explanation}")

            else:
                # Optional: Comment out to reduce noise
                # print(f"   {ticker} is stable ({pct_change*100:.2f}%).")
                pass

        except Exception as e:
            # print(f"   [!] Error analyzing {ticker}: {e}")
            continue

    print("\n---> Briefing Complete.")
    vault.close()

if __name__ == "__main__":
    run_narrator()