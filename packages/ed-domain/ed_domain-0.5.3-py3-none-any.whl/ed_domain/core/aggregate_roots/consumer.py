from dataclasses import dataclass
from uuid import UUID

from ed_domain.core.aggregate_roots.base_aggregate_root import \
    BaseAggregateRoot


@dataclass
class Consumer(BaseAggregateRoot):
    user_id: UUID
    first_name: str
    last_name: str
    phone_number: str
    profile_image_url: str
    email: str
    location_id: UUID

    def update_profile_image(self, new_image: str) -> None:
        self.profile_image_url = new_image

    def update_phone_number(self, new_phone_number: str) -> None:
        self.phone_number = new_phone_number

    def update_email(self, new_email: str) -> None:
        self.email = new_email
