from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ed_domain.core.base_domain_object import BaseDomainObject


@dataclass
class BaseEntity(BaseDomainObject):
    create_datetime: datetime
    update_datetime: datetime
    deleted: bool
    deleted_datetime: Optional[datetime]
