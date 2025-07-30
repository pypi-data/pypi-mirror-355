import dataclasses
from .stock import Stock


@dataclasses.dataclass
class MagicFormulaInput:
    stock: Stock
    market_cap: float
    ebit: float
    enterprise_value: float
    net_working_capital: float
    net_fixed_assets: float

    @staticmethod
    def from_stock(stock: Stock) -> "MagicFormulaInput":
        income_stmt = stock.income_statements.latest
        balance_sheet = stock.balance_sheets.latest
        if not (income_stmt and balance_sheet):
            return
        ebit = stock.income_statements.latest.ebit
        current_assets = balance_sheet.current_assets
        current_liabilities = balance_sheet.current_liabilities
        net_working_capital = current_assets - current_liabilities
        net_fixed_assets = balance_sheet.net_fixed_assets

        ev = stock.info.get("enterpriseValue")
        if not ev:
            ev = float(stock.info["marketCap"]) + balance_sheet.total_assets - balance_sheet.current_liabilities

        formula_input = MagicFormulaInput(
            stock=stock,
            market_cap=float(stock.info["marketCap"]),
            ebit=float(ebit),
            enterprise_value=float(ev),
            net_working_capital=float(net_working_capital),
            net_fixed_assets=float(net_fixed_assets),
        )
        return formula_input
