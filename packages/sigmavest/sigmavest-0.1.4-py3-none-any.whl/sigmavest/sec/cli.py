import typer
import json
import os

from .shortcuts import get_company_tickers_exchange
from .client import SecClient

app = typer.Typer()

@app.command()
def summary():
    """
    Provides a summary of SEC-related commands.
    """
    print("This is the `sec` command summary.")

@app.command()
def company_tickers_exchange(
    user_agent: str = typer.Option(None, help="User-Agent for SEC requests"),
    indent: int = typer.Option(None, help="Indentation level for JSON output"),
    output: str = typer.Option(
        None, "--output", "-o", help="Output file path to write JSON (optional)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite output file without confirmation"
    ),
):
    """
    Fetch and print the SEC company tickers exchange JSON.
    Optionally write the result to a JSON file.
    """
    data = get_company_tickers_exchange()
    json_str = json.dumps(data, indent=indent)
    if output:
        if os.path.exists(output) and not force:
            overwrite = typer.confirm(f"File '{output}' exists. Overwrite?", default=False)
            if not overwrite:
                print("Aborted. File not overwritten.")
                return
        with open(output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Written to {output}")
    else:
        print(json_str)

@app.command()
def cte(
    user_agent: str = typer.Option(None, help="User-Agent for SEC requests"),
    indent: int = typer.Option(None, help="Indentation level for JSON output"),
    output: str = typer.Option(
        None, "--output", "-o", help="Output file path to write JSON (optional)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite output file without confirmation"
    ),
):
    """
    Alias for company_tickers_exchange.
    """
    company_tickers_exchange(user_agent=user_agent, indent=indent, output=output, force=force)