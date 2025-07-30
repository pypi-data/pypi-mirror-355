import typer
from rich.console import Console
from rich.table import Table

from .cagr import calculate_cagr
from .gui import run_gui

app = typer.Typer()
console = Console()


@app.command()
def calculate(
    start: float = typer.Argument(..., help="Starting value of the investment"),
    end: float = typer.Argument(..., help="Ending value of the investment"),
    periods: float = typer.Argument(..., help="Number of periods (e.g. years) for the investment"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Display only the result skipping all details"),
):
    """Calculate Compound Annual Growth Rate (CAGR)"""
    try:
        cagr = calculate_cagr(start, end, periods)
        if quiet:
            print(cagr)
            return

        table = Table(
            title="CAGR Calculation Results",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")

        table.add_row("Starting Value", f"${start:,.2f}")
        table.add_row("Ending Value", f"${end:,.2f}")
        table.add_row("Number of Periods", f"{periods}")
        table.add_row("CAGR", f"{cagr:.2%}", style="bold green")

        console.print(table)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def gui():
    """Run the GUI for CAGR calculation"""
    run_gui()
