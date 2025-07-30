from typing import Optional

from ...dependency import resolve
from ..repository import PortfolioRepository
from .requests.portfolio import ListPortfoliosRequest, ListPortfoliosResponse


class PortfolioService:
    def __init__(self, repo: Optional[PortfolioRepository]):
        self.repo: PortfolioRepository = repo or resolve(PortfolioRepository)

    def list_portfolios(self, request: ListPortfoliosRequest) -> ListPortfoliosResponse:
        portfolios = self.repo.list_portfolios()
        return ListPortfoliosResponse(portfolios=portfolios)
