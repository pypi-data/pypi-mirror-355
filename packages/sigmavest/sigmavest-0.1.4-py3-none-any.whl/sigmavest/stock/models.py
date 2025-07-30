from sqlalchemy import create_engine, Column, Date, Float, Integer, String, Table, MetaData
from sqlalchemy import DateTime, func, Index


metadata = MetaData()

# Define the ticker_info table
ticker_info_table = Table(
    "ticker_info",
    metadata,
    Column("symbol", String, nullable=False),
    Column("key", String, nullable=False),
    Column("value", String, nullable=True),
    Column("updated_at", DateTime, nullable=False, server_default=func.now()),
    Column("id", Integer, primary_key=True, autoincrement=True),
)

ticker_info_table.append_constraint(Index("idx_ticker_info_symbol_key", "symbol", "key"))

# Define the balance_sheet table
balance_sheet_table = Table(
    "balance_sheet",
    metadata,
    Column("symbol", String, nullable=False),
    Column("submit_date", Date, nullable=False),
    Column("key", String, nullable=False),
    Column("value", Float, nullable=True),
    Column("id", Integer, primary_key=True, autoincrement=True),
)

balance_sheet_table.append_constraint(Index("idx_balance_sheet_submit_date_symbol", "submit_date", "symbol"))

income_statement_table = Table(
    "income_statement",
    metadata,
    Column("symbol", String, nullable=False),
    Column("submit_date", Date, nullable=False),
    Column("key", String, nullable=False),
    Column("value", Float, nullable=True),
    Column("id", Integer, primary_key=True, autoincrement=True),
)

income_statement_table.append_constraint(Index("idx_income_statement_submit_date_symbol", "submit_date", "symbol"))

cash_flow_statement_table = Table(
    "cash_flow_statement",
    metadata,
    Column("symbol", String, nullable=False),
    Column("submit_date", Date, nullable=False),
    Column("key", String, nullable=False),
    Column("value", Float, nullable=True),
    Column("id", Integer, primary_key=True, autoincrement=True),
)

cash_flow_statement_table.append_constraint(Index("idx_cash_flow_statement_submit_date_symbol", "submit_date", "symbol"))



def initialize(db_path: str = None):
    db_path = db_path or "tickers.db"
    engine = create_engine(f"sqlite:///{db_path}")

    # Create the table in the database
    metadata.create_all(engine)
    return engine
