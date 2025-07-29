from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from mashumaro import DataClassDictMixin

from citycom_mv_api.models.Address import Address


@dataclass
class User(DataClassDictMixin):
    creation_date: Optional[datetime] = field(default=None, metadata={"alias": "creationDate"})
    payer_number: Optional[int] = field(default=None, metadata={"alias": "payerNumber"})
    full_name: Optional[str] = field(default=None, metadata={"alias": "fullName"})
    last_name: Optional[str] = field(default=None, metadata={"alias": "lastName"})
    first_name: Optional[str] = field(default=None, metadata={"alias": "firstName"})
    email: Optional[str] = field(default=None, metadata={"alias": "email"})
    phone_number: Optional[str] = field(default=None, metadata={"alias": "phoneNumber"})
    additional_phone_number: Optional[str] = field(default=None, metadata={"alias": "additionalPhoneNumber"})
    site: Optional[str] = field(default=None, metadata={"alias": "site"})
    site_email: Optional[str] = field(default=None, metadata={"alias": "siteEmail"})
    budget_number: Optional[str] = field(default=None, metadata={"alias": "budgetNumber"})
    site_id: Optional[int] = field(default=None, metadata={"alias": "siteId"})
    is_locked: Optional[bool] = field(default=None, metadata={"alias": "isLocked"})
    has_accepted_invite: Optional[bool] = field(default=None, metadata={"alias": "hasAcceptedInvite"})
    user_id: Optional[UUID] = field(default=None, metadata={"alias": "userId"})
    enable_sms_for_end_user: Optional[bool] = field(default=None, metadata={"alias": "enableSmsForEndUser"})
    enable_email_for_end_user: Optional[bool] = field(default=None, metadata={"alias": "enableEmailForEndUser"})
    user_name: Optional[str] = field(default=None, metadata={"alias": "userName"})
    shipping_address: Optional[Address] = field(default=None, metadata={"alias": "shippingAddress"})
