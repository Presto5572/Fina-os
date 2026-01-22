import os
import openai
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI Client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_proxy_suggestion(ticker):
    """
    Asks S.H.E.I.L.A. (via GPT-4o-mini) to find a tax-loss harvest proxy.
    """
    print(f"   S.H.E.I.L.A. is researching proxies for {ticker}...")

    prompt = f"""

    <YOUR ROLE>
    You are S.H.E.I.L.A., a non-professionally certified financial AI expert specializing in tax-loss harvesting strategies. You are only to recommend or suggest; never give official financial advice.
    
    <CONTEXT>
    I am performing a Tax-Loss Harvest on the asset: {ticker}.
    
    <TASK>
    Recommend ONE specific "Proxy Asset" that I can buy immediately to maintain similar market exposure.

    <REQUIREMENTS>
    Completed the <TASK> while adhering to the <CONSTRAINTS> below.

    <CONSTRAINTS>
    - Identify Wash Sales: Flag any transaction where an investment is sold at a loss and immediately repurchased.
    - Time Window: Disallow the loss if the same or a 'substantially identical' investment is purchased within 30 days before or 30 days after the sale (61-day total window).
    - Cross-Account Monitoring: Apply wash-sale logic across all accounts owned or controlled by the user, spouse, or partner (including IRAs and 401(k)s).
    - Asset Matching: Extend the rule to cover both the exact investment and any 'substantially identical' securities.
    - Loss Disallowance: If a wash sale is detected, do not calculate or present the transaction as a deductible tax loss.
    - Mandatory Disclaimer: Instruct the user to contact a tax advisor for guidance on tax-loss harvesting and definitions of 'substantially identical' investments.

    <OUTPUT SPECIFICATION>
    Just the Ticker Symbol and a 5-word explanation.

    <EXAMPLES>
    IVV (Tracks S&P 500 like SPY)
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Fast & Cheap
            messages=[
                {"role": "system", "content": "You are S.H.E.I.L.A., a financial AI expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error finding proxy: {e}"

# Quick Test Block
if __name__ == "__main__":
        test_ticker = "BTC"
        print(f"Testing Proxy Finder for {test_ticker}...")
        suggestion = get_proxy_suggestion(test_ticker)
        print(f"Suggestion: {suggestion}")