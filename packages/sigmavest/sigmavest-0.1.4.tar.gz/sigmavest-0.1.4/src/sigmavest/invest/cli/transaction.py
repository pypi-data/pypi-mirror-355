import typer
from rich.console import Console
from rich.table import Table

from sigmavest.dependency import resolve
from sigmavest.invest.domain import Transaction
from sigmavest.invest.service import (
    BuySecurityRequest,
    ListTransactionsRequest,
    RecordDividendRequest,
    SellSecurityRequest,
    TransactionService,
)

app = typer.Typer()
console = Console()


@app.command(name="list")
def list_():
    """List transactions"""
    try:
        request = ListTransactionsRequest()
        service = resolve(TransactionService)
        transactions = service.list_transactions(request).transactions

        table = Table(
            title="Transactions",
            show_header=True,
            header_style="bold magenta",
        )

        field_names = Transaction.get_field_names()
        for f in field_names:
            table.add_column(f)

        for row in transactions:
            values = [getattr(row, field) for field in field_names]
            table.add_row(*map(str, values))

        console.print(table)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def buy(
    portfolio_id: str = typer.Argument(..., help="ID of the portfolio to which the transaction belongs"),
    ticker: str = typer.Argument(..., help="Ticker symbol of the asset to buy"),
    quantity: str = typer.Argument(..., help="Quantity of the asset to buy"),
    price: str = typer.Argument(..., help="Price per unit of the asset"),
    fees: str = typer.Argument(..., help="Transaction fees for the buy"),
    amount_paid: str = typer.Argument(..., help="Total amount paid for the transaction"),
    currency: str = typer.Argument(..., help=""),
    date: str = typer.Argument(..., help="Date of the transaction (YYYY-MM-DD)"),
):
    """Record a buy transaction"""
    try:
        request = BuySecurityRequest(
            portfolio_id=portfolio_id,
            security_id=ticker,
            quantity=quantity,  # type: ignore
            price=price,  # type: ignore
            fees=fees,  # type: ignore
            amount_paid=amount_paid,  # type: ignore
            currency=currency,
            date=date,
        )

        service = resolve(TransactionService)
        response = service.buy_serucity(request)

        console.print(f"[green]Transaction recorded: {response.transactions}[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def sell(
    portfolio_id: str = typer.Argument(..., help="ID of the portfolio to which the transaction belongs"),
    ticker: str = typer.Argument(..., help="Ticker symbol of the asset to buy"),
    quantity: str = typer.Argument(..., help="Quantity of the asset to buy"),
    price: str = typer.Argument(..., help="Price per unit of the asset"),
    fees: str = typer.Argument(..., help="Transaction fees for the buy"),
    amount_paid: str = typer.Argument(..., help="Total amount paid for the transaction"),
    currency: str = typer.Argument(..., help=""),
    date: str = typer.Argument(..., help="Date of the transaction (YYYY-MM-DD)"),
):
    """Record a sell transaction"""
    try:
        request = SellSecurityRequest(
            portfolio_id=portfolio_id,
            security_id=ticker,
            quantity=quantity,  # type: ignore
            price=price,  # type: ignore
            fees=fees,  # type: ignore
            amount_paid=amount_paid,  # type: ignore
            currency=currency,
            date=date,
        )

        service = resolve(TransactionService)
        response = service.sell_security(request)

        console.print(f"[green]Transaction recorded: {response.transactions}[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def dividend(
    portfolio_id: str = typer.Argument(..., help="ID of the portfolio to which the transaction belongs"),
    ticker: str = typer.Argument(..., help="Ticker symbol of the asset to buy"),
    quantity: str = typer.Argument(..., help="Quantity of the asset to buy"),
    price: str = typer.Argument(..., help="Price per unit of the asset"),
    fees: str = typer.Argument(..., help="Transaction fees for the buy"),
    amount_paid: str = typer.Argument(..., help="Total amount paid for the transaction"),
    currency: str = typer.Argument(..., help=""),
    date: str = typer.Argument(..., help="Date of the transaction (YYYY-MM-DD)"),
):
    """Record a dividend transaction"""
    try:
        request = RecordDividendRequest(
            portfolio_id=portfolio_id,
            security_id=ticker,
            quantity=quantity,  # type: ignore
            price=price,  # type: ignore
            fees=fees,  # type: ignore
            amount_paid=amount_paid,  # type: ignore
            currency=currency,
            date=date,
        )

        service = resolve(TransactionService)
        response = service.record_dividend(request)

        console.print(f"[green]Transaction recorded: {response.transactions}[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    