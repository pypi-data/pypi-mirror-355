from dataclasses import dataclass, field
from typing import Any, List, Optional
from uuid import UUID

from mashumaro import DataClassDictMixin

from citycom_mv_api.models.Address import Address
from citycom_mv_api.models.Meter import Meter


@dataclass
class Property(DataClassDictMixin):
    is_active: Optional[bool] = field(default=None, metadata={"alias": "isActive"})
    site: Optional[str] = field(default=None, metadata={"alias": "site"})
    meters: Optional[List["Meter"]] = field(default=None, metadata={"alias": "meters"})
    address: "Address" = field(default=None, metadata={"alias": "address"})
    property_id: int = field(default=0, metadata={"alias": "propertyId"})
    user_full_name: str = field(default="", metadata={"alias": "userFullName"})
    user_first_name: Optional[str] = field(default=None, metadata={"alias": "userFirstName"})
    user_last_name: Optional[str] = field(default=None, metadata={"alias": "userLastName"})
    number_of_persons: int = field(default=0, metadata={"alias": "numberOfPersons"})
    email: str = field(default="", metadata={"alias": "email"})
    user_id: UUID = field(default=None, metadata={"alias": "userId"})
    property_number: Optional[str] = field(default=None, metadata={"alias": "propertyNumber"})
    region_id: int = field(default=0, metadata={"alias": "regionId"})
    parent_properties: Optional[List[Any]] = field(default=None, metadata={"alias": "parentProperties"})
    negative_calculation_in_consumption_circle: bool = field(
        default=False, metadata={"alias": "negativeCalculationInConsumptionCircle"}
    )
