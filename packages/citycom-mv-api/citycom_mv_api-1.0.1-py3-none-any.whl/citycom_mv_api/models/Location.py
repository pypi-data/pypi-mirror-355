from dataclasses import dataclass, field
from typing import Optional

from mashumaro import DataClassDictMixin


@dataclass
class Location(DataClassDictMixin):
    latitude: Optional[float] = field(default=None, metadata={"alias": "latitude"})
    longitude: Optional[float] = field(default=None, metadata={"alias": "longitude"})
