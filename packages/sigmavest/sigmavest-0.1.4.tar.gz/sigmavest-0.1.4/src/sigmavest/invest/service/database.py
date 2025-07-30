from typing import Optional
from sigmavest.dependency import resolve
from sigmavest.settings import Settings
from .requests.database import (
    CreateDatabaseViewsRequest,
    CreateDatabaseViewsResponse,
    ImportDatabaseRequest,
    ImportDatabaseResponse,
    ExportDatabaseResponse,
    ExportDatatbaseRequest,
    QueryDatabaseResponse,
    QueryDatabaseRequest,
)
from ..repository import Database


class DatabaseService:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or resolve(Database)

    @property
    def default_data_path(self) -> str:
        settings = resolve(Settings)
        return settings.DATABASE_DATA_PATH

    @property
    def default_database(self) -> Database:
        return resolve(Database)

    def import_database(self, request: ImportDatabaseRequest) -> ImportDatabaseResponse:
        self.db.import_data(request.data_path)
        self.db.create_views()
        response = ImportDatabaseResponse()
        return response

    def export_database(self, request: ExportDatatbaseRequest) -> ExportDatabaseResponse:
        self.db.export_data(request.data_path, force=request.force)
        response = ExportDatabaseResponse()
        return response

    def query(self, request: QueryDatabaseRequest) -> QueryDatabaseResponse:
        query_result = self.db.db.execute(request.query)

        if query_result:
            column_names = [col[0] for col in query_result.description]  # type: ignore
            return QueryDatabaseResponse(column_names=column_names, rows=query_result.fetchall())
        else:
            return QueryDatabaseResponse(column_names=[], rows=[])

    def create_views(self, request: CreateDatabaseViewsRequest) -> CreateDatabaseViewsResponse:
        self.db.create_views()
        return CreateDatabaseViewsResponse()
