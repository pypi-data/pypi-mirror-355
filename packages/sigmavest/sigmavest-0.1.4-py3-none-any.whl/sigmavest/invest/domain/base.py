from dataclasses import fields


class DomainBase:
    @classmethod
    def get_field_names(cls):
        """
        Returns a list of field names for the Portfolio dataclass.
        """
        return [f.name for f in fields(cls)] # type: ignore
