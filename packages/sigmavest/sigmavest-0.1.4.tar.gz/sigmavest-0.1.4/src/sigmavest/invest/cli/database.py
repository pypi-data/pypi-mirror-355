import csv
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sigmavest.dependency import resolve
from sigmavest.invest.service import (
    CreateDatabaseViewsRequest,
    DatabaseService,
    ExportDatatbaseRequest,
    ImportDatabaseRequest,
    QueryDatabaseRequest,
)
from sigmavest.settings import Settings

app = typer.Typer()
console = Console()


@app.command(name="import")
def import_cli(
    data_path: Optional[str] = typer.Argument(None, help="Path to CSV data files to import."),
):
    """Import database from CSV files"""

    if data_path is None:
        settings = resolve(Settings)
        data_path = settings.DATABASE_DATA_PATH
    service = resolve(DatabaseService)
    request = ImportDatabaseRequest(data_path=data_path)
    request = service.import_database(request)

    console.print(f"[green]Dataabse imported from '{data_path}'.[/green]")


@app.command(name="export")
def export_cli(
    force: bool = typer.Option(False, help="Force export to non-empty directory."),
    data_path: Optional[str] = typer.Argument(None, help="Path to export CSV data to."),
):
    """Export database to CSV files"""

    if data_path is None:
        settings = resolve(Settings)
        data_path = settings.DATABASE_DATA_PATH
    service = resolve(DatabaseService)
    request = ExportDatatbaseRequest(data_path=data_path, force=force)
    request = service.export_database(request)

    console.print(f"[green]Dataabse exported to '{data_path}'.[/green]")


@app.command()
def query(
    query: str = typer.Argument(..., help="SQL query to execute against the DuckDB database"),
    output_file: str = typer.Option(None, help="File path to save the result to."),
):
    """
    Execute a SQL query against the DuckDB database.
    """

    try:
        service = resolve(DatabaseService)
        result = service.query(QueryDatabaseRequest(query=query))

        if result.rows:
            if output_file:
                with open(output_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(result.column_names)
                    writer.writerows(result.rows)

            else:
                table = Table(
                    title=query,
                    show_header=True,
                    header_style="bold magenta",
                )

                for f in result.column_names:
                    table.add_column(f)
                for row in result.rows:
                    table.add_row(*map(str, row))

                console.print(table)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def create_views():
    """Create database views"""
    service = resolve(DatabaseService)
    request = CreateDatabaseViewsRequest()
    request = service.create_views(request)

    console.print("[green]Database views created.[/green]")
