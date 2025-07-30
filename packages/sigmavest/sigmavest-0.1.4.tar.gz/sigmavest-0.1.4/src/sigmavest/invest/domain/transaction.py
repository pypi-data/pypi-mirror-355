from dataclasses import dataclass
import datetime
from decimal import Decimal
from .base import DomainBase

@dataclass
class Transaction(DomainBase):
    id: int | None
    date: datetime.date
    transaction_type: str
    portfolio_id: str
    ticker: str
    quantity: Decimal
    price: Decimal
    fees: Decimal
    amount_paid: Decimal
    currency: str
    exchange_rate: Decimal | None
