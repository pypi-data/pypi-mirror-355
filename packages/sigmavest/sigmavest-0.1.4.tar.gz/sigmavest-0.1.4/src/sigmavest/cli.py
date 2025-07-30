import typer
from .calc.cli import app as calc_app
from .sec.cli import app as sec_app
from .invest.cli import app as invest_app

app = typer.Typer()
app.add_typer(calc_app, name="calc")
app.add_typer(sec_app, name="sec")
app.add_typer(invest_app, name="invest")
