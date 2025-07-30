from ..dependency.container import Container
from .repository import PortfolioRepository, Database, TransactionRepository, SellAllocationsRepository
from .service import PortfolioService, TransactionService, DatabaseService


def register(c: Container):
    c.register_factory(Database, lambda c: Database.get_instance())

    # Register repositories
    c.register_factory(TransactionRepository, lambda c: TransactionRepository(c.resolve(Database)))
    c.register_factory(PortfolioRepository, lambda c: PortfolioRepository(c.resolve(Database)))
    c.register_factory(SellAllocationsRepository, lambda c: SellAllocationsRepository(c.resolve(Database)))

    # Register services
    c.register_factory(TransactionService, lambda c: TransactionService(c.resolve(TransactionRepository)))
    c.register_factory(PortfolioService, lambda c: PortfolioService(c.resolve(PortfolioRepository)))
    c.register_factory(DatabaseService, lambda c: DatabaseService())

