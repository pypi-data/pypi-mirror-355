from abc import ABCMeta, abstractmethod
from uuid import UUID

from ed_domain.core.entities.waypoint import Waypoint, WaypointStatus
from ed_domain.persistence.async_repositories.abc_async_generic_repository import \
    ABCAsyncGenericRepository


class ABCAsyncWaypointRepository(
    ABCAsyncGenericRepository[Waypoint],
    metaclass=ABCMeta,
):
    @abstractmethod
    async def update_waypoint_status(
        self, id: UUID, status: WaypointStatus
    ) -> bool: ...
