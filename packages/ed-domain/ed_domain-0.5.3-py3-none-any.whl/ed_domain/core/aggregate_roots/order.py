from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID

from ed_domain.core.aggregate_roots.base_aggregate_root import \
    BaseAggregateRoot
from ed_domain.core.entities.bill import Bill, BillStatus
from ed_domain.core.entities.parcel import Parcel


class OrderStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PICKED_UP = "picked_up"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Order(BaseAggregateRoot):
    business_id: UUID
    consumer_id: UUID
    order_number: str
    order_status: OrderStatus
    latest_time_of_delivery: datetime
    bill: Bill
    parcel: Parcel
    distance_in_km: float
    driver_id: Optional[UUID] = None
    customer_rating: Optional[int] = None
    expected_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None
    picked_up_datetime: Optional[datetime] = None
    completed_datetime: Optional[datetime] = None

    def set_customer_rating(self, rating: int) -> None:
        if not 1 <= rating <= 5:
            raise ValueError("Customer rating has to be between 1 and 5.")

    def update_bill_status(self, new_status: str) -> None:
        if new_status not in BillStatus:
            raise ValueError(f"Invalid bill status: {new_status}")

        self.bill.bill_status = BillStatus(new_status)

    def assign_driver(self, driver_id: UUID) -> None:
        if self.order_status != OrderStatus.PENDING:
            raise ValueError(
                "Cannot assign driver to an order that is not pending.")
        self.driver_id = driver_id
        self.update_status(OrderStatus.IN_PROGRESS)

    def pick_up_order(self) -> None:
        if self.order_status != OrderStatus.IN_PROGRESS:
            raise ValueError(
                "Cannot complete an order that is not in progress.")
        self.picked_up_datetime = datetime.now(UTC)
        self.update_status(OrderStatus.PICKED_UP)

    def complete_order(self) -> None:
        if self.order_status != OrderStatus.PICKED_UP:
            raise ValueError("Cannot complete an order that is not picked up.")
        self.completed_datetime = datetime.now(UTC)
        self.actual_delivery_time = datetime.now(UTC)
        self.update_status(OrderStatus.COMPLETED)

    def cancel_order(self) -> None:
        if self.order_status in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}:
            raise ValueError(
                "Cannot cancel an order that is already completed or cancelled."
            )
        self.update_status(OrderStatus.CANCELLED)

    def update_status(self, new_status: OrderStatus) -> None:
        if new_status not in OrderStatus:
            raise ValueError(f"Invalid order status: {new_status}")

        self.order_status = new_status
