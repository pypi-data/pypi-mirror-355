from abc import ABCMeta

from ed_domain.core.aggregate_roots.location import Location
from ed_domain.persistence.repositories.abc_generic_repository import \
    ABCGenericRepository


class ABCLocationRepository(
    ABCGenericRepository[Location],
    metaclass=ABCMeta,
):
    ...
