from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options


@dataclass
class AuthError(DataClassDictMixin):
    error_type: str = field(metadata=field_options(alias="error"))
    error_summary: str = field(metadata=field_options(alias="error_description"))
