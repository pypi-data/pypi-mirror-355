from pydantic import BaseModel
from .base import BaseRequest, BaseResponse


class ImportDatabaseRequest(BaseModel, BaseRequest):
    data_path: str


class ImportDatabaseResponse(BaseModel, BaseResponse):
    pass


class ExportDatatbaseRequest(BaseModel, BaseRequest):
    data_path: str
    force: bool = False


class ExportDatabaseResponse(BaseModel, BaseResponse):
    pass


class QueryDatabaseRequest(BaseModel, BaseRequest):
    query: str


class QueryDatabaseResponse(BaseModel, BaseResponse):
    column_names: list[str]
    rows: list


class CreateDatabaseViewsRequest(BaseModel, BaseRequest):
    pass

class CreateDatabaseViewsResponse(BaseModel, BaseResponse):
    pass
