from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from mashumaro import DataClassDictMixin


@dataclass
class MeterReadings(DataClassDictMixin):
    meter_id: Optional[int] = field(default=None, metadata={"alias": "meterId"})
    consumption_current_month: Optional[float] = field(default=None, metadata={"alias": "consumptionCurrentMonth"})
    last_reading: Optional[float] = field(default=None, metadata={"alias": "lastReading"})
    last_reading_date: Optional[datetime] = field(default=None, metadata={"alias": "lastReadingDate"})
