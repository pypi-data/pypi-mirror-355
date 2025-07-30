from typing import Iterable
from pydantic import BaseModel
from .base import BaseRequest, BaseResponse
from ...domain import Portfolio


class ListPortfoliosRequest(BaseModel, BaseRequest):
    pass


class ListPortfoliosResponse(BaseModel, BaseResponse):
    portfolios: Iterable[Portfolio]
