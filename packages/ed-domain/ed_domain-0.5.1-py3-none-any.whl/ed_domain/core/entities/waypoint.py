from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from ed_domain.core.entities.base_entity import BaseEntity


class WaypointStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"


class WaypointType(StrEnum):
    PICK_UP = "pick_up"
    DROP_OFF = "drop_off"


@dataclass
class Waypoint(BaseEntity):
    delivery_job_id: UUID
    order_id: UUID
    expected_arrival_time: datetime
    actual_arrival_time: datetime
    sequence: int
    waypoint_type: WaypointType
    waypoint_status: WaypointStatus

    def update_status(self, new_status: WaypointStatus) -> None:
        self.waypoint_status = new_status

    def update_eta(self, new_eta: datetime) -> None:
        self.eta = new_eta
