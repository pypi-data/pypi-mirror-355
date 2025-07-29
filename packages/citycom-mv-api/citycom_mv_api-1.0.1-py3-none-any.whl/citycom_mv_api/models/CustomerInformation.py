from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from mashumaro import DataClassDictMixin

from citycom_mv_api.models.Address import Address
from citycom_mv_api.models.Property import Property


@dataclass
class CustomerInformation(DataClassDictMixin):
    language: Optional[None] = field(default=None, metadata={"alias": "language"})
    roles: Optional[List[str]] = field(default=None, metadata={"alias": "roles"})
    properties: Optional[List[Property]] = field(default=None, metadata={"alias": "properties"})
    user_name: Optional[str] = field(default=None, metadata={"alias": "userName"})
    allow_to_send_to_customer: Optional[bool] = field(default=None, metadata={"alias": "allowToSendToCustomer"})
    manager_sites: Optional[List[Any]] = field(default=None, metadata={"alias": "managerSites"})
    creation_date: Optional[datetime] = field(default=None, metadata={"alias": "creationDate"})
    payer_number: Optional[int] = field(default=None, metadata={"alias": "payerNumber"})
    full_name: Optional[str] = field(default=None, metadata={"alias": "fullName"})
    last_name: Optional[str] = field(default=None, metadata={"alias": "lastName"})
    first_name: Optional[str] = field(default=None, metadata={"alias": "firstName"})
    email: Optional[str] = field(default=None, metadata={"alias": "email"})
    phone_number: Optional[str] = field(default=None, metadata={"alias": "phoneNumber"})
    additional_phone_number: Optional[str] = field(default=None, metadata={"alias": "additionalPhoneNumber"})
    site: Optional[str] = field(default=None, metadata={"alias": "site"})
    site_id: Optional[int] = field(default=None, metadata={"alias": "siteId"})
    is_locked: Optional[bool] = field(default=None, metadata={"alias": "isLocked"})
    has_accepted_invite: Optional[bool] = field(default=None, metadata={"alias": "hasAcceptedInvite"})
    user_id: Optional[UUID] = field(default=None, metadata={"alias": "userId"})
    enable_sms_for_end_user: Optional[bool] = field(default=None, metadata={"alias": "enableSMSForEndUser"})
    enable_email_for_end_user: Optional[bool] = field(default=None, metadata={"alias": "enableEmailForEndUser"})
    shipping_address: Optional[Address] = field(default=None, metadata={"alias": "shippingAddress"})
