import os
import openai
import json
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, IntPrompt
from rich import box

load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
console = Console()

def save_plan_to_file(plan_data):
    """Saves the JSON plan to a readable text file."""
    filename = "investment_blueprint.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(filename, "w") as f:
        f.write(f"S.H.E.I.L.A. | STRATEGIC INVESTMENT BLUEPRINT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("="*50 + "\n")
        f.write(f"Archetype: {plan_data.get('archetype', 'N/A')}\n")
        f.write(f"Rationale: {plan_data.get('rationale', 'N/A')}\n\n")
        
        f.write("--- TARGET ALLOCATION ---\n")
        for asset, pct in plan_data.get('allocation', {}).items():
            f.write(f"{asset}: {pct}\n")
            
        f.write("\n--- THE BLUEPRINT ---\n")
        for item in plan_data.get('blueprint', []):
            f.write(f"{item['ticker']} ({item['name']}): {item['allocation']} - {item['reason']}\n")
            
        f.write("\n" + "="*50 + "\n")
    
    console.print(f"\n[bold green]✅ Blueprint saved to: {os.path.abspath(filename)}[/bold green]")

# ... imports remain the same ...

# ... imports remain the same ...

def run_architect():
    console.clear()
    
    # HEADER UI
    title_text = Text("THE ARCHITECT", style="bold cyan")
    subtitle_text = Text("Strategic Investment Planner", style="dim white")
    console.print(Panel.fit(
        Align.center(title_text + "\n" + subtitle_text),
        border_style="cyan",
        padding=(1, 2)
    ))
    
    console.print("\n[bold]I need to scan your financial profile to design your framework.[/bold]\n")
    
    # 1. THE INTERVIEW
    try:
        age = IntPrompt.ask("[cyan]1. What is your current age?[/cyan]")
        capital = Prompt.ask("[cyan]2. Investment Capital[/cyan] (e.g. $5,000)")
        
        # GOAL
        console.print("\n[cyan]3. Primary Goal[/cyan] [dim](Choose a number)[/dim]")
        console.print("   [1] Retirement")
        console.print("   [2] House Downpayment")
        console.print("   [3] Passive Income")
        console.print("   [4] Aggressive Growth")
        console.print("   [5] College Fund")
        goal_choice = IntPrompt.ask("   [cyan]Select[/cyan]", choices=["1", "2", "3", "4", "5"], default=1)
        goal_map = {1: "Retirement", 2: "House Downpayment", 3: "Passive Income", 4: "Aggressive Growth", 5: "College Fund"}
        final_goal = goal_map[goal_choice]

        # ASSET UNIVERSE
        console.print("\n[cyan]4. Investment Universe[/cyan] [dim](Structure)[/dim]")
        console.print("   [1] ETFs Only [dim](Simple)[/dim]")
        console.print("   [2] ETFs + Mutual Funds [dim](Classic)[/dim]")
        console.print("   [3] Core + Individual Stocks [dim](Active)[/dim]")
        console.print("   [4] Safety First [dim](Bonds/CDs)[/dim]")
        
        univ_choice = IntPrompt.ask("   [cyan]Select[/cyan]", choices=["1", "2", "3", "4"], default=1)
        univ_map = {
            1: "ETFs Only",
            2: "ETFs and Mutual Funds",
            3: "ETFs and High-Conviction Individual Stocks",
            4: "ETFs, Bonds, CDs, and Treasuries"
        }
        universe = univ_map[univ_choice]

        # RISK
        console.print("\n[yellow]5. Market Crash Simulation[/yellow] [dim](Market drops 20%)[/dim]")
        console.print("   [1] Sell everything")
        console.print("   [2] Do nothing")
        console.print("   [3] Buy more")
        risk_choice = IntPrompt.ask("   [cyan]Action[/cyan]", choices=["1", "2", "3"], default=2)
        risk_map = {1: "Sell / Low Tolerance", 2: "Hold / Medium Tolerance", 3: "Buy More / High Tolerance"}
        final_risk = risk_map[risk_choice]
        
        horizon = IntPrompt.ask("\n[cyan]6. Time Horizon (Years)[/cyan]")
        
    except KeyboardInterrupt:
        return

    # 2. THE LOGIC (Broad & Creative)
    prompt = f"""
    <ROLE>
    You are S.H.E.I.L.A., a strategic financial architect. You use broad institutional asset classes.
    
    <USER PROFILE>
    - Age: {age}
    - Capital: {capital}
    - Goal: {final_goal}
    - Allowed Assets: {universe}
    - Risk Reaction: {final_risk}
    - Horizon: {horizon} years
    
    <TASK>
    Create a "Portfolio Framework" in pure JSON format.
    
    <ASSET CLASS DEFINITIONS>
    Instead of just "Stocks/Bonds", use these BROAD categories for the Allocation Table:
    1. **Equities** (Stocks, ETFs, Mutual Funds)
    2. **Fixed Income** (Bonds, Treasuries, CDs)
    3. **Real Assets / Alts** (REITs, Commodities, Gold - Optional, only if fits goal)
    4. **Cash & Equivalents** (Money Market, HYSA)
    
    <SELECTION RULES (CRITICAL)>
    1. **DIVERSITY INJECTION:** - If the user wants Growth, do NOT just say QQQ/NVDA. Look at **Healthcare (VHT), Semis (SOXX), Cybersec (CIBR), or Cons. Discretionary (XLY)**.
       - If the user wants Income, do NOT just say SCHD. Look at **Realty Income (O), Utilities (XLU), or covered calls**.
       - **AVOID CLICHÉS:** Unless it is absolutely perfect, try to find the *second* best option to ensure diversity (e.g., instead of SPY, maybe suggest SPLG or VOO).
    
    2. **RESPECT THE UNIVERSE:** - If "ETFs Only", no single stocks.
       - If "Individual Stocks", pick 2 high-quality names that fit the theme (e.g. LOW for housing, JPM for finance).
       
    <JSON STRUCTURE>
    {{
        "archetype": "Creative Name",
        "rationale": "One sentence explanation.",
        "allocation": {{
            "Equities": "X%",
            "Fixed Income": "Y%",
            "Real Assets": "Z%",
            "Cash": "W%"
        }},
        "blueprint": [
            {{
                "ticker": "SYMBOL", 
                "name": "Asset Name",
                "allocation": "X%",
                "reason": "Specific reason."
            }}
        ]
    }}
    """
    
    print("\n")
    data = None
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]S.H.E.I.L.A. is calculating broad exposures...[/bold cyan]"),
        transient=True
    ) as progress:
        progress.add_task("thinking", total=None)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"}, 
                messages=[
                    {"role": "system", "content": "You are a creative institutional investor. Output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7 # High creativity to break the "NVDA/QQQ" loop
            )
            raw_json = response.choices[0].message.content.strip()
            data = json.loads(raw_json)
            
        except Exception as e:
            console.print(f"[red]Error generating plan: {e}[/red]")
            return

    # 3. THE RENDER
    
    # Table 1: Broad Allocation
    alloc_table = Table(title="Target Allocation", box=None, padding=(0, 2), show_header=True) 
    alloc_table.add_column("Broad Category", justify="right", style="cyan")
    alloc_table.add_column("Weight", justify="left", style="bold green")

    for asset, pct in data.get('allocation', {}).items():
        # Only show non-zero categories to keep it clean
        if pct != "0%" and pct != "0":
            alloc_table.add_row(asset, pct)

    # Table 2: Vehicles
    blue_table = Table(title="\nStrategic Vehicles", box=box.SIMPLE_HEAD, padding=(0, 2), expand=False)
    blue_table.add_column("Ticker", style="bold yellow", width=8)
    blue_table.add_column("Name", style="white", min_width=20)
    blue_table.add_column("%", justify="center", style="green", width=6)
    blue_table.add_column("Rationale", style="dim white")

    for item in data.get('blueprint', []):
        blue_table.add_row(
            item.get('ticker', 'N/A'),
            item.get('name', 'Asset'),
            item.get('allocation', '0%'),
            item.get('reason', '')
        )

    console.print(Panel(
        Align.center(
            f"[bold underline]{data.get('archetype', 'Investor')}[/bold underline]\n"
            f"[italic]{data.get('rationale')}[/italic]\n\n"
        ),
        title="[bold cyan]Strategic Blueprint[/bold cyan]",
        border_style="green",
        padding=(1, 2)
    ))
    
    console.print(Align.center(alloc_table))
    console.print(Align.center(blue_table))
    
    save_plan_to_file(data)

if __name__ == "__main__":
    run_architect()
# ---> python3 -m spokes.proxy_finder
# ---> python3 -m spokes.architect