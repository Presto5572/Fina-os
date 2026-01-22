import os
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def run_architect():
    print("\n<<< THE ARCHITECT: STRATEGIC PLANNER >>>\n")
    print("I need to learn about you to design your portfolio framework.")
    
    # 1. The Interview (Input)
    try:
        age = input("1. What is your current age? ")
        investment_amount = input("2. How much money are you investing today? (e.g., $5,000): ")
        goal = input("3. What is the primary goal for this money? (e.g., Retirement, House Downpayment, Passive Income): ")
        risk_reaction = input("4. If the market drops 20% tomorrow, do you (A) Sell everything, (B) Do nothing, or (C) Buy more? [A/B/C]: ")
        risk_pref = input("5. On a scale from Conservative, Moderate, to Aggressive, how would you describe your risk tolerance? ")
        horizon = input("6. How many years until you need to spend this money? ")
    except KeyboardInterrupt:
        return

    print("\n---> S.H.E.I.L.A. is drafting your Investment Policy Statement (IPS)...")

    # 2. The Logic (AI Processing)
    prompt = f"""
    <ROLE>
    You are S.H.E.I.L.A., a conservative, logic-driven financial planner. You follow Boglehead (passive indexing) philosophies.
    You are NOT a financial advisor. Always include a disclaimer.
    
    <USER PROFILE>
    - Age: {age}
    - Investment Amount: {investment_amount}(e.g. $5,000)
    - Goal: {goal} (e.g., Retirement, House Downpayment, Passive Income, College Fund)
    - Risk Reaction: {risk_reaction} (A=Panic, B=Neutral, C=Aggressive)
    - Risk Preference: {risk_pref} (Conservative, Moderate, Aggressive)
    - Time Horizon: {horizon} years
    

    <TASK>
    Create a "Portfolio Framework" for this user.
    1. Define their "Investor Archetype" (e.g., Aggressive Accumulator, Preservationist).
    2. Recommend a specific Asset Allocation (Stocks, Bonds, Alternatives, Cash) in percentages.
    3. Recommend specific low-cost ETFs (Vanguard/Blackrock) to fill those buckets.
    4. Explain WHY this mix fits their goal.
    
    <OUTPUT FORMAT>
    >> Archetype: [Name]
    >> Target Allocation: [X]% Stocks / [Y]% Bonds / [Z]% Alternatives / [W]% Cash
    >> The Blueprint:
      - [Ticker] ([Name]): [Percentage]% (Reason)
      - [Ticker] ([Name]): [Percentage]% (Reason)
        ...
    >> Rationale: [One sentence explanation]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Use GPT-4 for "Thinking" tasks if available, or mini
            messages=[
                {"role": "system", "content": "You are an expert asset allocator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        plan = response.choices[0].message.content.strip()
        
        print("\n" + "="*40)
        print(plan)
        print("="*40 + "\n")
        
        # Future Step: We could save this "Target Allocation" to the database
        # vault.save_target(plan) 
        
    except Exception as e:
        print(f"Error generating plan: {e}")

if __name__ == "__main__":
    run_architect()