import typer
from rich.console import Console
import pandas as pd

from sigmavest.dependency import resolve
from sigmavest.magicformula import MagicFormulaScraper
from sigmavest.invest.service.database import DatabaseService
from sigmavest.settings import Settings

app = typer.Typer()
console = Console()
settings = resolve(Settings)


@app.command()
def scrape(
    username: str = typer.Option(None, "--username", "-u", help="Username."),
    password: str = typer.Option(None, "--password", "-p", help="User password."),
    output_file: str = typer.Option(None, "--output-file", "-o", help="Output file name."),
    output_table: str = typer.Option(None, "--output-table", "-t", help="Output table name."),
    rename_headers: bool = typer.Option(False, "--rename-headers", "-r", help="Rename headers."),
    min_market_cap: int = typer.Option(
        settings.MAGIC_FORMULA_MIN_MARKET_CAP, "--min-market-cap", "-m", min=1, help="Miniumum market capitalization."
    ),
):
    username = username or settings.MAGIC_FORMULA_USERNAME
    password = password or settings.MAGIC_FORMULA_PASSWORD

    try:
        if not username or not password:
            raise ValueError("User credentials are not provided.")
        scraper = MagicFormulaScraper(username, password)
        results = scraper.scrape(min_market_cap)
        if rename_headers:
            results.columns = ["company_name", "ticker", "market_cap", "price_from_date", "recent_quarter_date"]
        results.index.name = "pos"
        results["min_market_cap"] = min_market_cap
        results["taken_at"] = pd.Timestamp.now(tz="UTc")
        if output_file:
            results.to_csv(output_file)
            console.print(f"[green]Results exported to '{output_file}'[/green]")
        if output_table:
            service = resolve(DatabaseService)
            results.to_sql(output_table, service.db.db)  # type: ignore
            console.print(f"[green]Results saved to database table '{output_table}'[/green]")
        console.print(results.iloc[:,:5])
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
