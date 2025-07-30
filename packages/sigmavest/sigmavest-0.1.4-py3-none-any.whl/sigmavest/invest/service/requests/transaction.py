from decimal import Decimal
from typing import Iterable
from pydantic import BaseModel, Field, field_validator, condate
from .base import BaseRequest, BaseResponse
from ...domain import Transaction
from ...repository import PortfolioRepository
from ....dependency import resolve


class ListTransactionsRequest(BaseModel, BaseRequest):
    pass


class ListTransactionsResponse(BaseModel, BaseResponse):
    transactions: Iterable[Transaction]


class CreateTransactionBaseRequest(BaseModel, BaseRequest):
    portfolio_id: str = Field(..., min_length=1, max_length=20, examples=["Portfolio1"])
    security_id: str = Field(..., min_length=1, max_length=10, examples=["AAPL"])
    quantity: Decimal = Field(..., gt=0, decimal_places=8, examples=["10.5"])
    price: Decimal = Field(..., gt=0, decimal_places=4, examples=["150.35"])
    fees: Decimal = Field(..., decimal_places=4, examples=["1.24"])
    amount_paid: Decimal = Field(..., decimal_places=2, examples=["1568.23"])
    currency: str = Field(..., min_length=3, max_length=3)
    date: condate() = Field(..., examples=["2025-12-25"])  # type: ignore

    @field_validator("portfolio_id")
    @classmethod
    def validate_portfolio_id(cls, value):
        portfolio_repo = resolve(PortfolioRepository)
        if not portfolio_repo.exists(value):
            msg = f"'{value}' is not a valid portfolio ID."
            raise ValueError(msg)
        return value

    def to_domain_model(self) -> Transaction:
        return Transaction(
            id=None,
            date=self.date,
            transaction_type="BUY",
            portfolio_id=self.portfolio_id,
            ticker=self.security_id,
            quantity=self.quantity,
            price=self.price,
            fees=self.fees,
            amount_paid=self.amount_paid,
            currency=self.currency,
            exchange_rate=None,
        )


class BuySecurityRequest(CreateTransactionBaseRequest):
    pass


class BuySecurityResponse(BaseModel, BaseResponse):
    transactions: list[Transaction]


class SellSecurityRequest(CreateTransactionBaseRequest):
    def to_domain_model(self) -> Transaction:
        transaction = super().to_domain_model()
        transaction.transaction_type = "SELL"
        transaction.price = -transaction.price
        transaction.amount_paid = -transaction.amount_paid
        return transaction


class SellSecurityResponse(BaseModel, BaseResponse):
    transactions: list[Transaction]


class RecordDividendRequest(CreateTransactionBaseRequest):
    def to_domain_model(self) -> Transaction:
        transaction = super().to_domain_model()
        transaction.transaction_type = "DIVIDEND"
        transaction.price = -transaction.price
        transaction.amount_paid = -transaction.amount_paid
        return transaction


class RecordDividendResponse(BaseModel, BaseResponse):
    transactions: list[Transaction]
