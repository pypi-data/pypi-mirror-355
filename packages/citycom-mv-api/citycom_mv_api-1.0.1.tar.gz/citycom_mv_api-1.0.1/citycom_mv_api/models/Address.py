from dataclasses import dataclass, field
from typing import Optional

from mashumaro import DataClassDictMixin


@dataclass
class Address(DataClassDictMixin):
    address_id: Optional[int] = field(default=None, metadata={"alias": "addressId"})
    city: Optional[str] = field(default=None, metadata={"alias": "city"})
    street: Optional[str] = field(default=None, metadata={"alias": "street"})
    street_number: Optional[str] = field(default=None, metadata={"alias": "streetNumber"})
    apartment: Optional[str] = field(default=None, metadata={"alias": "apartment"})
    address_str: Optional[str] = field(default=None, metadata={"alias": "addressStr"})
    postal_code: Optional[str] = field(default=None, metadata={"alias": "postalCode"})
    mail_box: Optional[str] = field(default=None, metadata={"alias": "mailBox"})
    name: Optional[str] = field(default=None, metadata={"alias": "name"})
