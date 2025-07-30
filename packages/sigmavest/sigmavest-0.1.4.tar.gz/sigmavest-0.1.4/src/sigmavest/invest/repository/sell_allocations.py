from decimal import Decimal
from typing import Optional

from .db import Database


class SellAllocationsRepository:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database.get_instance()

    @classmethod
    def get_instance(cls, db=None):
        """
        Factory method to get a repository instance.
        """
        return cls(db)

    def allocate_sell(self, portfoliio_id: str, ticker: str, sell_transaction_id: int, quantity: Decimal):
        open_buys = self.get_open_buys(portfoliio_id, ticker)

        remaining_qty_to_allocate = quantity
        next_allocation_id = self.get_last_id() + 1
        print(open_buys)
        print(next_allocation_id)
        allocations = []
        for buy_txn_id, qty in open_buys:
            allocate_qty = remaining_qty_to_allocate
            if remaining_qty_to_allocate > qty:
                allocate_qty = qty
            remaining_qty_to_allocate -= allocate_qty
            allocations.append((next_allocation_id, sell_transaction_id, buy_txn_id, allocate_qty))
            next_allocation_id += 1
            if not remaining_qty_to_allocate:
                break
        if remaining_qty_to_allocate:
            raise ValueError(f"Cannot sale {quantity} stock. Only {sum(qty for _, qty in open_buys)} are available.")
        self.create_allocations(allocations)

    def create_allocations(self, allocations):
        query = (
            "INSERT INTO sell_allocations (id, sell_transaction_id, buy_transaction_id, quantity) VALUES (?, ?, ?, ?)"
        )
        self.db.execute_many(query, allocations)

    def get_open_buys(self, portfolio_id, ticker):
        query = """
            SELECT buys.id,
                   CAST(buys.quantity - COALESCE(alloc.sold_quantity, 0) AS DECIMAL(20,8)) AS quantity
              FROM transactions buys
              LEFT JOIN (
                         SELECT SUM(quantity) AS sold_quantity,
                                buy_transaction_id
                           FROM sell_allocations
                          GROUP BY buy_transaction_id
                        ) alloc ON alloc.buy_transaction_id=buys.id
             WHERE buys.ticker=?
                   AND buys.portfolio_id=?
                   AND buys.transaction_type = 'BUY'
                   AND CAST(buys.quantity - COALESCE(alloc.sold_quantity, 0) AS DECIMAL(20,8)) > 0
             ORDER BY buys.date ASC,
                      buys.id ASC
        """
        return self.db.execute(query, [ticker, portfolio_id])

    def get_last_id(self):
        id = self.db.db.execute("SELECT MAX(id) FROM sell_allocations").fetchone()[0]  # type: ignore
        return id or 0
