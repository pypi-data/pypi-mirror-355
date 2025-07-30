from dataclasses import dataclass
from uuid import UUID

from ed_domain.core.entities.base_entity import BaseEntity


@dataclass
class Webhook(BaseEntity):
    business_id: UUID
    url: str
