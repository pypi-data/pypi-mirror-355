from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from mashumaro import DataClassDictMixin

from citycom_mv_api.models.Location import Location
from citycom_mv_api.models.MeterProperty import MeterProperty
from citycom_mv_api.models.User import User


@dataclass
class Meter(DataClassDictMixin):
    meter_id: Optional[int] = field(default=None, metadata={"alias": "meterId"})
    site_title: Optional[str] = field(default=None, metadata={"alias": "siteTitle"})
    meter_type: Optional[int] = field(default=None, metadata={"alias": "meterType"})
    number: Optional[str] = field(default=None, metadata={"alias": "number"})
    external_transmission_id: Optional[str] = field(default=None, metadata={"alias": "externalTransmissionID"})
    full_name: Optional[str] = field(default=None, metadata={"alias": "fullName"})
    address_string: Optional[str] = field(default=None, metadata={"alias": "addressString"})
    property_number: Optional[str] = field(default=None, metadata={"alias": "propertyNumber"})
    external_water_card_id: Optional[str] = field(default=None, metadata={"alias": "externalWaterCardId"})
    parent_number: Optional[str] = field(default=None, metadata={"alias": "parentNumber"})
    last_reading_date: Optional[datetime] = field(default=None, metadata={"alias": "lastReadingDate"})
    last_reading_value: Optional[str] = field(default=None, metadata={"alias": "lastReadingValue"})
    last_repeater_id: Optional[str] = field(default=None, metadata={"alias": "lastRepeaterId"})
    tariff_name: Optional[str] = field(default=None, metadata={"alias": "tariffName"})
    include: Optional[str] = field(default=None, metadata={"alias": "include"})
    size_title: Optional[str] = field(default=None, metadata={"alias": "sizeTitle"})
    model_type_name: Optional[str] = field(default=None, metadata={"alias": "modelTypeName"})
    type: Optional[int] = field(default=None, metadata={"alias": "type"})
    is_rtu: Optional[bool] = field(default=None, metadata={"alias": "isRTU"})
    meter_size_id: Optional[int] = field(default=None, metadata={"alias": "meterSizeId"})
    multiplier: Optional[float] = field(default=None, metadata={"alias": "multiplier"})
    equipment_id: Optional[int] = field(default=None, metadata={"alias": "equipmentId"})
    site_id: Optional[int] = field(default=None, metadata={"alias": "siteId"})
    location: Optional[Location] = field(default=None, metadata={"alias": "location"})
    property: Optional[MeterProperty] = field(default=None, metadata={"alias": "property"})
    user: Optional[User] = field(default=None, metadata={"alias": "user"})
    creation_date: Optional[datetime] = field(default=None, metadata={"alias": "creationDate"})
    tariff_id: Optional[int] = field(default=None, metadata={"alias": "tariffId"})
    is_enabled: Optional[bool] = field(default=None, metadata={"alias": "isEnabled"})
    utilization_type: Optional[str] = field(default=None, metadata={"alias": "utilizationType"})
    utilization_type_id: Optional[int] = field(default=None, metadata={"alias": "utilizationTypeId"})
    installation_date: Optional[datetime] = field(default=None, metadata={"alias": "installationDate"})
    exclude_from_site_consumption: Optional[bool] = field(
        default=None, metadata={"alias": "excludeFromSiteConsumption"}
    )
    kashrout: Optional[str] = field(default=None, metadata={"alias": "kashrout"})
    first_reading_value: Optional[float] = field(default=None, metadata={"alias": "firstReadingValue"})
    model_type_id: Optional[int] = field(default=None, metadata={"alias": "modelTypeId"})
    first_or_last_dma_layer: Optional[bool] = field(default=None, metadata={"alias": "firstOrLastDmaLayer"})
