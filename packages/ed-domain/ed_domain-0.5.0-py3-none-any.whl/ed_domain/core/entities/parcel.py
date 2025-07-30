from dataclasses import dataclass
from enum import StrEnum

from ed_domain.core.entities.base_entity import BaseEntity


class ParcelSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class Parcel(BaseEntity):
    size: ParcelSize
    length: float
    width: float
    height: float
    weight: float
    fragile: bool
