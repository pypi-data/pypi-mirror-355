from dataclasses import dataclass, field
from typing import List, Optional

from mashumaro import DataClassDictMixin

from citycom_mv_api.models.Bucket import Bucket


@dataclass
class ConsumptionHistoryData(DataClassDictMixin):
    date: Optional[str] = field(default=None, metadata={"alias": "name"})
    series: Optional[List[Bucket]] = field(default=None, metadata={"alias": "series"})



