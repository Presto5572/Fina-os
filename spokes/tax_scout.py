import yfinance as yf
import pandas as pd
import sqlite3
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.align import Align
from rich import box
from core.database import SheilaVault

# --- CONFIGURATION ---
LOSS_THRESHOLD = -0.05       # Trigger alert if asset is down 5%
MIN_HARVEST_AMOUNT = 100.00  # Only harvest if loss is > $100 (Save on fees/effort)
# ---------------------

console = Console()

def fetch_current_prices(tickers):
    """
    Fetches live prices for a list of tickers using yfinance.
    """
    if not tickers:
        return {}
    
    # Map crypto if needed (Yahoo requires -USD suffix)
    search_tickers = []
    for t in tickers:
        if t in ['BTC', 'ETH', 'LTC']:
            search_tickers.append(f"{t}-USD")
        else:
            search_tickers.append(t)
            
    try:
        # Download 1 day of data
        data = yf.download(search_tickers, period="1d", progress=False)['Close']
        
        prices = {}
        
        # If we requested 1 ticker, it returns a Series
        if len(search_tickers) == 1:
            val = data.iloc[-1].item() if not data.empty else None
            prices[search_tickers[0]] = val
        else:
            # Multi-ticker DataFrame
            last_row = data.iloc[-1]
            for t in search_tickers:
                try:
                    price = last_row[t]
                    if pd.notna(price):
                        prices[t] = price
                except KeyError:
                    pass
                    
        return prices
    except Exception as e:
        console.print(f"[red]API Error:[/red] {e}")
        return {}

def run_tax_scout():
    console.clear()
    
    # HEADER UI
    console.print(Panel.fit(
        Align.center("[bold green]TAX SCOUT[/bold green]\n[dim]Loss Harvesting Engine[/dim]"),
        border_style="green",
        padding=(1, 2)
    ))
    
    vault = SheilaVault()
    console.print("\n[bold]1. Scanning Portfolio Database...[/bold]")
    
    # 1. GET HOLDINGS (FIXED COLUMN NAME)
    try:
        vault.cursor.execute("SELECT ticker, quantity, cost_basis FROM holdings")
        holdings = vault.cursor.fetchall()
    except sqlite3.OperationalError as e:
        console.print(f"[bold red]Database Error:[/bold red] {e}")
        console.print("[yellow]Tip: Run 'clean_db.py' and 'setup_server.py' to reset your schema if this persists.[/yellow]")
        return
    
    if not holdings:
        console.print("[yellow]   No holdings found in database. Run 'setup_server.py' or check DB.[/yellow]")
        return

    # Clean list of tickers
    active_tickers = [h[0] for h in holdings if h[0] and h[0] != 'UNKNOWN']
    
    # 2. FETCH PRICES
    current_prices = {}
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[cyan]Fetching live market data for {task.total} assets...[/cyan]"),
        transient=True
    ) as progress:
        task = progress.add_task("download", total=len(active_tickers))
        
        raw_prices = fetch_current_prices(active_tickers)
        
        for _ in active_tickers:
            time.sleep(0.05) 
            progress.advance(task)
            
        current_prices = raw_prices

    # 3. CALCULATE & RENDER
    console.print("\n[bold]2. Analysis Results[/bold]\n")
    
    table = Table(title="Harvest Opportunities", box=box.SIMPLE_HEAD, show_lines=False)
    table.add_column("Asset", style="bold white")
    table.add_column("Position", justify="right")
    table.add_column("Current Price", justify="right")
    table.add_column("Gain/Loss", justify="right")
    table.add_column("Status", justify="center")
    
    harvest_candidates = []
    
    for row in holdings:
        ticker, qty, total_cost_basis = row
        
        if not ticker or ticker == 'UNKNOWN': 
            continue

        # Derived Average Cost (Price per share)
        # Handle division by zero just in case
        avg_cost = total_cost_basis / qty if qty else 0
            
        lookup_ticker = f"{ticker}-USD" if ticker in ['BTC', 'ETH'] else ticker
        live_price = current_prices.get(lookup_ticker)
        
        if live_price:
            market_val = live_price * qty
            # We use the explicit Total Cost Basis from DB
            gain_loss_amt = market_val - total_cost_basis
            
            # Calculate % change
            gain_loss_pct = (live_price - avg_cost) / avg_cost if avg_cost > 0 else 0
            
            # FORMATTING
            color = "green" if gain_loss_amt >= 0 else "red"
            fmt_amt = f"[{color}]${gain_loss_amt:,.2f}[/{color}]"
            fmt_pct = f"[{color}]{gain_loss_pct*100:+.2f}%[/{color}]"
            
            # DECISION LOGIC
            status = "[dim]Hold[/dim]"
            
            if gain_loss_pct <= LOSS_THRESHOLD and gain_loss_amt <= -MIN_HARVEST_AMOUNT:
                status = "[bold red]HARVEST[/bold red]"
                harvest_candidates.append((ticker, gain_loss_amt))
            elif gain_loss_amt < 0:
                status = "[yellow]Watch[/yellow]"
            elif gain_loss_amt > 0:
                status = "[green]Healthy[/green]"
            
            table.add_row(
                ticker,
                f"${total_cost_basis:,.0f}",
                f"${live_price:,.2f}",
                f"{fmt_amt} ({fmt_pct})",
                status
            )
        else:
            table.add_row(ticker, "---", "---", "---", "[bold red]⚠️ Data Err[/bold red]")

    console.print(Align.center(table))
    
    # 4. ACTION REPORT
    if harvest_candidates:
        total_potential_loss = sum([x[1] for x in harvest_candidates])
        
        summary_panel = Panel(
            f"[bold]Detected {len(harvest_candidates)} opportunities.[/bold]\n"
            f"Total Tax Deduction Available: [bold red]${total_potential_loss:,.2f}[/bold red]\n\n"
            "[italic]Recommendation: Review these positions for replacement.[/italic]",
            title="[bold red]ACTION REQUIRED[/bold red]",
            border_style="red"
        )
        console.print("\n")
        console.print(Align.center(summary_panel))
    else:
        console.print("\n[bold green]✅ Portfolio is efficient. No significant losses to harvest.[/bold green]")

    vault.close()

if __name__ == "__main__":
    run_tax_scout()