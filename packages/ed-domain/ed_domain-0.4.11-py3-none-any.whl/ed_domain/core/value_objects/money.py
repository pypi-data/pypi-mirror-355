from dataclasses import dataclass
from enum import StrEnum

from ed_domain.core.value_objects.base_value_object import BaseValueObject


class Currency(StrEnum):
    ETB = "etb"
    USD = "usd"


@dataclass
class Money(BaseValueObject):
    value: float
    currency: Currency
