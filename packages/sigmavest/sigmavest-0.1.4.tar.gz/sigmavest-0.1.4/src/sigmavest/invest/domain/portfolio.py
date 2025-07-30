from dataclasses import dataclass, fields
from .base import DomainBase

@dataclass
class Portfolio(DomainBase):
    id: int
    name: str
    description: str = ""

    @classmethod
    def get_field_names(cls):
        """
        Returns a list of field names for the Portfolio dataclass.
        """
        return [f.name for f in fields(cls)]
