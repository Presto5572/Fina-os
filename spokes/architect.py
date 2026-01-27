import os
import openai
from dotenv import load_dotenv # Load environment variables
from datetime import datetime # For timestamping
from rich.console import Console # Rich console for better CLI UX
from rich.panel import Panel # For bordered panels
from rich.table import Table # For tabular data
from rich.markdown import Markdown # For rendering markdown
from rich.progress import Progress, SpinnerColumn, TextColumn # For progress spinners
from rich.prompt import Prompt, IntPrompt # For user prompts

load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
console = Console()

def save_plan_to_file(plan_text):
    """Saves the generated plan to a local text file."""
    filename = "investment_blueprint.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(filename, "w") as f:
        f.write(f"S.H.E.I.L.A. | STRATEGIC INVESTMENT BLUEPRINT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("="*50 + "\n\n")
        f.write(plan_text)
        f.write("\n\n" + "="*50 + "\n")
        f.write("DISCLAIMER: This is an AI-generated simulation for educational purposes only.\n")
    
    console.print(f"\n[bold green] Blueprint saved to: {os.path.abspath(filename)}[/bold green]")

def run_architect():
    console.clear()
    console.print(Panel.fit("[bold cyan]THE ARCHITECT[/bold cyan]\n[dim]Strategic Investment Planner[/dim]", border_style="cyan"))
    
    console.print("\n[bold]I need to scan your financial profile to design your framework.[/bold]\n")
    
    # 1. The UX-Enhanced Interview
    try:
        age = IntPrompt.ask("[cyan]1. What is your current age?[/cyan]")
        capital = Prompt.ask("[cyan]2. How much money are you investing today?[/cyan] (e.g. $5,000)")
        goal = Prompt.ask("[cyan]3. Primary Goal[/cyan]", choices=["Retirement", "House", "Passive Income", "Growth"], default="Retirement")
        
        console.print("\n[yellow]4. Market Crash Simulation[/yellow]")
        console.print("[dim]   The market drops 20% tomorrow. You lose $5,000.[/dim]")
        risk_reaction = Prompt.ask("[cyan]   Do you[/cyan]", choices=["Sell", "Hold", "Buy More"], default="Hold")
        
        horizon = IntPrompt.ask("\n[cyan]5. Time Horizon (Years)[/cyan]")
        
    except KeyboardInterrupt:
        return

    # 2. The Logic (AI Processing)
    prompt = f"""
    <ROLE>
    You are S.H.E.I.L.A., a conservative, logic-driven financial planner. You follow Boglehead (passive indexing) philosophies.
    
    <USER PROFILE>
    - Age: {age}
    - Capital: {capital}
    - Goal: {goal}
    - Risk Reaction: {risk_reaction}
    - Horizon: {horizon} years
    
    <TASK>
    Create a "Portfolio Framework" (Investment Policy Statement).
    
    <OUTPUT FORMATTING RULES>
    1. Use Markdown headers (###) for sections.
    2. Use a Markdown Table for the "Target Allocation".
    3. Use a Markdown Table for "The Blueprint" (Columns: Ticker, Name, %, Rationale).
    4. Keep the rationale concise.
    
    <OUTPUT STRUCTURE>
    ### Investor Archetype: [Name]
    
    ### Target Allocation
    | Asset Class | Percentage |
    | :--- | :--- |
    | Stocks | X% |
    | Bonds | Y% |
    | ... | ... |

    ### The Blueprint
    | Ticker | Asset Name | Allocation | Logic |
    | :--- | :--- | :--- | :--- |
    | **VTI** | Total US Stock | 40% | Core growth engine |
    
    ### Strategy Note
    [One sentence explanation]
    
    *Disclaimer: Uncertified recommendation simulation only.*
    """

    print("\n")
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]S.H.E.I.L.A. is drafting your Investment Policy Statement...[/bold cyan]"),
        transient=True
    ) as progress:
        progress.add_task("thinking", total=None)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial planning engine. Output only Markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            plan = response.choices[0].message.content.strip()
            
        except Exception as e:
            console.print(f"[red]Error generating plan: {e}[/red]")
            return

    # 3. The Render (Beautiful Markdown)
    console.print(Panel(Markdown(plan), title="[bold cyan]Your Strategic Blueprint[/bold cyan]", border_style="green"))
    save_plan_to_file(plan)

if __name__ == "__main__":
    run_architect()