from typing import Optional
import requests


class SecClient:
    def __init__(self, api_key: Optional[str]=None, user_agent: Optional[str]=None):
        self.api_key = api_key or "sigmavest.1.0.1@pypi.org"
        self.base_url = "https://www.sec.gov"
        self.user_agent = user_agent or "sigmavest.1.0.1@pypi.org"

    def get_filings(self, cik: str, form_type: Optional[str] = None):
        """
        Fetch filings for a given CIK and optional form type.
        """
        url = f"{self.base_url}/cgi-bin/browse-edgar"
        params = {"action": "getcompany", "CIK": cik, "type": form_type, "output": "atom", "count": 100}
        headers = {"User-Agent": f"SigmaVest/{self.api_key}"}

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        return response.text

    def get_company_tickers_exchange(self):
        header = {
            "User-Agent": self.user_agent
        }
        cik_ticker_exchange_url = "https://www.sec.gov/files/company_tickers_exchange.json"
        response = requests.get(cik_ticker_exchange_url, headers=header)
        response.raise_for_status()
        return response.json()
