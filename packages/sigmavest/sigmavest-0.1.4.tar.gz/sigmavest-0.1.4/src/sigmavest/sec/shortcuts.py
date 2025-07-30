from collections import namedtuple
from .client import SecClient


def get_company_tickers_exchange() -> list:
    """
    Fetch the company tickers and their corresponding exchanges from the SEC.

    Returns:
        list: A list of namedtuples, containing `cik`, `name`, `ticker`, and `exchange` information.

    Example:
    ```python
        from sigmavest.sec.shortcuts import get_company_tickers_exchange
        tickers = get_company_tickers_exchange()
        print(tickers[0])
        # Output:
        # SecCompanyTicker(cik=789019, name='MICROSOFT CORP', ticker='MSFT', exchange='Nasdaq')
    ```
    """
    client = SecClient()
    data = client.get_company_tickers_exchange()
    Ticker = namedtuple("SecCompanyTicker", data["fields"])
    tickers = [Ticker(*row) for row in data["data"]]
    return tickers
