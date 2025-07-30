from typing import Optional

from ...dependency import resolve
from ..repository import SellAllocationsRepository, TransactionRepository
from .requests.transaction import (
    BuySecurityRequest,
    BuySecurityResponse,
    ListTransactionsRequest,
    ListTransactionsResponse,
    RecordDividendRequest,
    RecordDividendResponse,
    SellSecurityRequest,
    SellSecurityResponse,
)


class TransactionService:
    def __init__(self, repo: Optional[TransactionRepository]):
        self.repo: TransactionRepository = repo or resolve(TransactionRepository)

    def list_transactions(self, request: ListTransactionsRequest) -> ListTransactionsResponse:
        transactions = self.repo.list_transactions()
        response = ListTransactionsResponse(transactions=transactions)
        return response

    def buy_serucity(self, request: BuySecurityRequest) -> BuySecurityResponse:
        transaction = request.to_domain_model()
        transaction = self.repo.add(transaction)
        response = BuySecurityResponse(transactions=[transaction])
        return response

    def sell_security(self, request: SellSecurityRequest) -> SellSecurityResponse:
        """
        Sell security by creating a sell transaction and allocating the quantity to buy transactions.
        """

        db = self.repo.db
        sell_allocations_repo = resolve(SellAllocationsRepository)
        with db.transaction():
            sell_txn = request.to_domain_model()
            sell_txn = self.repo.add(sell_txn)
            assert sell_txn.id is not None, (
                "Cannot record sell allocations as newly created sell transaction has no id set."
            )
            sell_allocations_repo.allocate_sell(sell_txn.portfolio_id, sell_txn.ticker, sell_txn.id, sell_txn.quantity)
        return SellSecurityResponse(transactions=[sell_txn])

    def record_dividend(self, request: RecordDividendRequest) -> RecordDividendResponse:
        transaction = request.to_domain_model()
        transaction = self.repo.add(transaction)
        response = RecordDividendResponse(transactions=[transaction])
        return response
