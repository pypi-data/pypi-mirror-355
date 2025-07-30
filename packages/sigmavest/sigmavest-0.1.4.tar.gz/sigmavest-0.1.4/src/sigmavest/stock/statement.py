from typing import List
from sigmavest.utils import split_at_capitals

class Statement(dict):
    """
    A class to represent a financial statement as a dictionary.

    This class extends the built-in `dict` class to provide a structure for
    financial statements, allowing for easy access and manipulation of financial data.

    Example usage:
    ```python
    from yfinance import Ticker
    from sigmavest.stock.statement import Statement

    ticker = Ticker("ANF")
    statement = Statement(ticker.balance_sheet.iloc[:,0])
    print(statement["Stockholders Equity"])  # Accessing Total Assets
    ```
    """

    METRIC_NAME_ALIASES = {
        "NetDebt": ["NetDebt", "TotalDebt"],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self  # Allow attribute-style access

    def __getitem__(self, key):
        key_aliases = self._get_metric_aliases(key)
        for k in key_aliases:
            if k in self:
                return super().__getitem__(k)
        return super().__getitem__(key)

    @classmethod
    def register_metric_name_alias(cls, metric_name: str, aliases: str | List[str]):
        """
        Register one or more aliases for a given metric name.

        Args:
            metric_name (str): The name of the metric to register aliases for.
            aliases (list): A list of aliases for the metric.
        """
        if not isinstance(aliases, list):
            aliases = [aliases]
        if metric_name not in cls.METRIC_NAME_ALIASES:
            cls.METRIC_NAME_ALIASES[metric_name] = []
        new_aliases = [alias for alias in aliases if alias not in cls.METRIC_NAME_ALIASES[metric_name]]
        cls.METRIC_NAME_ALIASES[metric_name].extend(new_aliases)

    def _get_metric_aliases(self, metric_name: str) -> List[str]:
        """
        Get the aliases for a given metric name.

        Args:
            metric_name (str): The name of the metric to get aliases for.

        Returns:
            list: A list of aliases for the metric.
        """
        aliases = self.METRIC_NAME_ALIASES.get(metric_name) or [metric_name]
        splits = [split_at_capitals(alias) for alias in aliases]
        return aliases + splits
