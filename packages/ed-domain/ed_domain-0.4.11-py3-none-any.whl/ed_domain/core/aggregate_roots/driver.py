from dataclasses import dataclass
from uuid import UUID

from ed_domain.core.aggregate_roots.base_aggregate_root import \
    BaseAggregateRoot
from ed_domain.core.entities.car import Car


@dataclass
class Driver(BaseAggregateRoot):
    user_id: UUID
    first_name: str
    last_name: str
    profile_image: str
    phone_number: str
    location_id: UUID
    car: Car
    email: str
    available: bool = False

    def update_availability(self, available: bool) -> None:
        self.available = available

    def update_current_location(self, new_location_id: UUID) -> None:
        self.location_id = new_location_id

    def update_profile_image(self, new_image: str) -> None:
        self.profile_image = new_image

    def update_email(self, new_email: str) -> None:
        self.email = new_email

    def update_phone_number(self, new_phone_number: str) -> None:
        self.phone_number = new_phone_number
