import requests
from bs4 import BeautifulSoup
import pandas as pd


class MagicFormulaScraper:
    BASE_URL = "https://magicformulainvesting.com"

    HOME_URL = f"{BASE_URL}/"
    LOGIN_URL = f"{BASE_URL}/Account/LogOn"
    FORM_URL = f"{BASE_URL}/Screening/StockScreening"
    RESULTS_URL = f"{BASE_URL}/Screening/StockScreening"

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"

    def __init__(self, username, password, *, session=None):
        self._session = session or self._get_session()
        self._username = username
        self._password = password

    def scrape(self, min_market_cap=50) -> pd.DataFrame:
        self._login()
        html = self._retrieve_screening_results_page(min_market_cap)
        return self._scrape_results(html)

    def _get_session(self):
        session = requests.Session()
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": self.HOME_URL,
            "DNT": "1",  # Do Not Track
        }
        session.headers.update(headers)
        return session

    def _acquire_request_validation_token(self, url):
        login_page_response = self._session.get(url)
        login_page_response.raise_for_status()
        soup = BeautifulSoup(login_page_response.text, "html.parser")
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token_input:
            raise Exception(f"Acquire request validatiln token failed. Page structure changed? {url}")
        token = token_input["value"]  # type: ignore
        return token

    def _login(self):
        token = self._acquire_request_validation_token(self.LOGIN_URL)
        login_data = {
            "__RequestVerificationToken": token,
            "Email": self._username,
            "Password": self._password,
            "RememberMe": "false",
        }
        login_response = self._session.post(
            self.LOGIN_URL,
            data=login_data,
            headers={
                "Referer": self.LOGIN_URL,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        # Check if login was successful
        if "Welcome" not in login_response.text:
            raise Exception("Login failed. Please check your credentials.")

    def _retrieve_screening_results_page(self, min_market_cap=50):
        """Submit the stock screening form"""
        token = self._acquire_request_validation_token(self.FORM_URL)

        # Prepare form data (adjust parameters as needed)
        form_data = {
            "MinimumMarketCap": str(min_market_cap),  # Minimum market cap in millions
            "Select30": "false",
            "stocks": "Get Stocks",
            "__RequestVerificationToken": token,
        }
        # Submit the form
        form_response = self._session.post(
            self.FORM_URL,
            data=form_data,
            headers={
                "Referer": self.FORM_URL,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        form_response.raise_for_status()

        # Check if submission was successful
        if "Company Name (in alphabetical order)" not in form_response.text:
            raise Exception("Form submission failed. Unexpected result returned.")

        return form_response.text

    def _scrape_results(self, page_content):
        """Scrape the results page and return data"""
        soup = BeautifulSoup(page_content, "html.parser")

        # Find the results table - adjust selector based on actual page structure
        table = soup.find("table", {"class": "divheight screeningdata"})

        if not table:
            raise Exception("Results table not found. The page structure may have changed.")

        # Extract headers
        headers = [th.text.strip() for th in table.find("thead").find_all("th")]  # type: ignore

        # Extract rows
        rows = []
        for tr in table.find("tbody").find_all("tr"):  # type: ignore
            rows.append([td.text.strip() for td in tr.find_all("td")])  # type: ignore

        df = pd.DataFrame(rows, columns=headers)
        return df
