from typing import Any
import yfinance as yf
from sigmavest.cache.file_cache import FileCache


class BaseStockRepository:
    cache_key: str
    cache_dir: str = "cache"
    cache_ttl: int = 3600000
    ticker_property: str

    def get(self, ticker: yf.Ticker) -> Any:
        cache = self.get_cache(ticker)
        data = cache.get(self.cache_key, not_found_callback=lambda: getattr(ticker, self.ticker_property))
        return data

    def get_cache(self, ticker: yf.Ticker) -> dict:
        cache = FileCache(cache_dir=self.cache_dir, ttl=self.cache_ttl, topic=ticker.ticker)
        return cache


class StockInfoRepository(BaseStockRepository):
    cache_key = "info"
    ticker_property = "info"


class BalanceSheetsRepository(BaseStockRepository):
    cache_key = "balance_sheet"
    ticker_property = "balance_sheet"


class IncomeStatementsRepository(BaseStockRepository):
    cache_key = "income_statement"
    ticker_property = "income_stmt"


class CashFlowStatementsRepository(BaseStockRepository):
    cache_key = "cashflow"
    ticker_property = "cashflow"
