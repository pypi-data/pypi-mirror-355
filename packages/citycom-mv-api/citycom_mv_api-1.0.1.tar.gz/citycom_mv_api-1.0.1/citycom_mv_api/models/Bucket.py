from dataclasses import dataclass, field
from typing import Optional

from mashumaro import DataClassDictMixin


@dataclass
class Bucket(DataClassDictMixin):
    consumption_type: Optional[str] = field(default=None, metadata={"alias": "name"})
    value: Optional[float] = field(default=None, metadata={"alias": "value"})
