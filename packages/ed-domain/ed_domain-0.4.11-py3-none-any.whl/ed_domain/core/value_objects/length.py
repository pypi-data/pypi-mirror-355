from dataclasses import dataclass
from enum import StrEnum

from ed_domain.core.value_objects.base_value_object import BaseValueObject


class Unit(StrEnum):
    KG = "kg"
    G = "g"


@dataclass
class Length(BaseValueObject):
    value: float
    currency: Unit
