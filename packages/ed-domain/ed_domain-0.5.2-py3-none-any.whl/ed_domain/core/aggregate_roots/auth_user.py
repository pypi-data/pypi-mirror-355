from dataclasses import dataclass
from typing import Optional

from ed_domain.core.aggregate_roots.base_aggregate_root import \
    BaseAggregateRoot


@dataclass
class AuthUser(BaseAggregateRoot):
    first_name: str
    last_name: str
    password_hash: str
    verified: bool
    logged_in: bool
    email: Optional[str] = None
    phone_number: Optional[str] = None

    def verify(self) -> None:
        self.verified = True

    def log_out(self) -> None:
        self.logged_in = False

    def log_in(self) -> None:
        self.logged_in = True

    def update_phone_number(self, new_phone_number: str) -> None:
        self.phone_number = new_phone_number

    def update_email(self, new_email: str) -> None:
        self.email = new_email

    def update_password_hash(self, new_password_hash: str) -> None:
        self.password_hash = new_password_hash
