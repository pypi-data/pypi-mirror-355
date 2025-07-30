import importlib
import typer
from rich.console import Console

from sigmavest.dependency import resolve

from ...settings import Settings
import os

app = typer.Typer()

modules = ["portfolio", "transaction", "database", "magicformula"]

for module_name in modules:
    m = importlib.import_module(f".{module_name}", __package__)
    module_app = m.app
    app.add_typer(module_app, name=module_name)

console = Console()


@app.callback()
def main(ctx: typer.Context, db_path: str = typer.Option(None, help="Path to the database file")):
    settings = resolve(Settings)
    if "SIGMAVEST_DB_PATH" in os.environ:
        settings.DATABASE_PATH = os.environ["SIGMAVEST_DB_PATH"]
    if db_path is not None:
        settings.DATABASE_PATH = db_path


@app.command()
def summary():
    """
    Provides a summary of TRACK-related commands.
    """
    print("This is the `track` command summary.")
