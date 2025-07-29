from dataclasses import dataclass
from uuid import UUID

from ed_domain.core.aggregate_roots.base_aggregate_root import \
    BaseAggregateRoot
from ed_domain.core.entities.api_key import ApiKey


@dataclass
class Business(BaseAggregateRoot):
    user_id: UUID
    business_name: str
    owner_first_name: str
    owner_last_name: str
    phone_number: str
    email: str
    location_id: UUID
    api_keys: list[ApiKey]

    def add_api_key(self, api_key: ApiKey) -> None:
        self.api_keys.append(api_key)

    def update_business_name(self, new_name: str) -> None:
        self.business_name = new_name

    def update_phone_number(self, new_phone_number: str) -> None:
        self.phone_number = new_phone_number

    def update_email(self, new_email: str) -> None:
        self.email = new_email
