from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from ed_domain.core.entities.base_entity import BaseEntity


class OtpType(StrEnum):
    VERIFY_EMAIL = "VERIFY_EMAIL"
    VERIFY_PHONE_NUMBER = "VERIFY_PHONE_NUMBER"
    LOGIN = "LOGIN"
    PICK_UP = "PICK_UP"
    DROP_OFF = "DROP_OFF"


@dataclass
class Otp(BaseEntity):
    user_id: UUID
    value: str
    otp_type: OtpType
    expiry_datetime: datetime
