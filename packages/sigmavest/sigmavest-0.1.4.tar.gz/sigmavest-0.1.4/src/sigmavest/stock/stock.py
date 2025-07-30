from typing import Any
import pandas as pd
import yfinance as yf

from sigmavest.stock.repository import (
    BalanceSheetsRepository,
    BaseStockRepository,
    CashFlowStatementsRepository,
    IncomeStatementsRepository,
    StockInfoRepository,
)


def get_first_existing_key(data: dict, keys: list, default=...):
    """
    Get the value of the first key that exists in the dictionary.

    :param data: The dictionary to search.
    :param keys: A list of keys to check in order.
    :return: The value of the first existing key, or None if none of the keys exist.
    """
    for key in keys:
        if key in data:
            return data[key]
    if default is not ...:
        return default
    raise KeyError(f"None of the keys {keys} exist in the dictionary.")


class WithRepository:
    repository_class: type = None
    _data: Any = None
    _repo: BaseStockRepository = None
    _ticker: yf.Ticker = None

    @property
    def data(self) -> Any:
        if not self._data:
            self._data = self.fetch_object()
        return self._data

    @property
    def ticker(self) -> yf.Ticker:
        if not self._ticker:
            raise ValueError("Ticker is not set.")
        return self._ticker

    def fetch_object(self) -> Any:
        repo = self.get_repo()
        obj = repo.get(self.ticker)
        if obj is None:
            raise ValueError(f"Failed to fetch object for ticker {self.ticker.ticker}")
        return obj

    def get_repo(self) -> BaseStockRepository:
        if not self._repo:
            self._repo = self.repository_class()
        return self._repo


class CashFlowStatement(dict):
    pass


class CashFlowStatements(WithRepository):
    repository_class = CashFlowStatementsRepository
    _data: pd.DataFrame = None

    def __init__(self, ticker: yf.Ticker):
        self._ticker = ticker

    @property
    def dates(self) -> list:
        return self.data.keys()

    @property
    def latest(self) -> CashFlowStatement:
        if not self.dates:
            return None
        latest_date = sorted(self.dates, reverse=True)[0]
        return self.data[latest_date]

    def fetch_object(self) -> dict:
        obj: pd.DataFrame = super().fetch_object()
        obj_dict = {dt: CashFlowStatement(bs) for dt, bs in obj.to_dict().items()}
        return obj_dict


class IncomeStatement(dict):
    @property
    def ebit(self):
        try:
            return get_first_existing_key(self, ["EBIT", "EBITDA"])
        except KeyError:
            pass
        try:
            return self.total_revenue - self.sga_expense
        except KeyError:
            pass
        return self.net_income - self.intest_expense - self.tax_provision

    @property
    def net_income(self):
        return self["Net Income"]

    @property
    def total_revenue(self):
        return self["Total Revenue"]

    @property
    def sga_expense(self):
        return self["Selling General And Administrative Expense"]

    @property
    def intest_expense(self):
        return self["Interest Expense"]

    @property
    def tax_provision(self):
        return self.get("Tax Provision", 0)


class IncomeStatements(WithRepository):
    repository_class = IncomeStatementsRepository
    _data: pd.DataFrame = None

    def __init__(self, ticker: yf.Ticker):
        self._ticker = ticker

    @property
    def dates(self) -> list:
        return self.data.keys()

    @property
    def latest(self) -> IncomeStatement:
        if not self.dates:
            return None
        latest_date = sorted(self.dates, reverse=True)[0]
        return self.data[latest_date]

    def fetch_object(self) -> dict:
        obj: pd.DataFrame = super().fetch_object()
        obj_dict = {dt: IncomeStatement(bs) for dt, bs in obj.to_dict().items()}
        return obj_dict


class BalanceSheet(dict):
    @property
    def total_assets(self):
        return float(self["Total Assets"])

    @property
    def current_liabilities(self):
        keys = [
            "Current Liabilities",
            "Total Current Liabilities Net Minority Interest",
            "Current Debt And Capital Lease Obligation",
            "Payables And Accrued Expenses",
        ]
        return get_first_existing_key(self, keys, 0)

    @property
    def current_assets(self):
        keys = ["Current Assets", "Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"]
        return float(get_first_existing_key(self, keys))

    @property
    def net_fixed_assets(self):
        keys = ["Net PPE", "Net Property, Plant and Equipment"]
        return float(get_first_existing_key(self, keys))


class BalanceSheets(WithRepository):
    repository_class = BalanceSheetsRepository
    _data: pd.DataFrame = None

    def __init__(self, ticker: yf.Ticker):
        self._ticker = ticker

    @property
    def dates(self) -> list:
        return self.data.keys()

    @property
    def latest(self) -> BalanceSheet:
        """
        Fetch the latest balance sheet from the database.
        """
        if not self.dates:
            return None
        latest_date = sorted(self.dates, reverse=True)[0]
        return self.data[latest_date]

    def fetch_object(self) -> dict:
        obj: pd.DataFrame = super().fetch_object()
        obj_dict = {dt: BalanceSheet(bs) for dt, bs in obj.to_dict().items()}
        return obj_dict


class StockInfo(dict):
    _repo: StockInfoRepository = None

    def __init__(self, ticker: yf.Ticker):
        self._ticker = ticker
        super().__init__(self._get_info())

    @property
    def ticker(self):
        return self._ticker

    def _get_info(self) -> dict:
        repo = self.get_repo()
        info = repo.get(self.ticker)
        if not info:
            raise ValueError(f"Failed to fetch info for ticker {self.ticker.ticker}")
        return info

    def get_repo(self) -> StockInfoRepository:
        if not self._repo:
            self._repo = StockInfoRepository()
        return self._repo


class Stock:
    _ticker: yf.Ticker = None
    _info: StockInfo = None
    _balance_sheets: BalanceSheets = None
    _income_statements: IncomeStatements = None
    _cash_flow_statements: CashFlowStatements = None

    def __init__(self, symbol: str):
        self._symbol = symbol

    @property
    def ticker(self) -> yf.Ticker:
        if not self._ticker:
            self._ticker = yf.Ticker(self._symbol)
        return self._ticker

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def info(self) -> dict:
        if not self._info:
            self._info = StockInfo(self.ticker)
        return self._info

    @property
    def balance_sheets(self) -> BalanceSheets:
        if not self._balance_sheets:
            self._balance_sheets = BalanceSheets(self.ticker)
        return self._balance_sheets

    @property
    def income_statements(self) -> IncomeStatements:
        if not self._income_statements:
            self._income_statements = IncomeStatements(self.ticker)
        return self._income_statements

    @property
    def cash_flow_statements(self) -> CashFlowStatements:
        if not self._cash_flow_statements:
            self._cash_flow_statements = CashFlowStatements(self.ticker)
        return self._cash_flow_statements

    @property
    def _info_repo(self) -> StockInfoRepository:
        if not self._info_repo_:
            self._info_repo_ = StockInfoRepository()
        return self._info_repo_
