import typer
from .cagr.cli import app as cagr_app

app = typer.Typer()

app.add_typer(cagr_app, name="cagr")

@app.command()
def summary():
    """
    Provides a summary of calculation logic.
    """
    print("This is the `calc` command summary.")
