from abc import ABCMeta

from ed_domain.core.entities.api_key import ApiKey
from ed_domain.persistence.async_repositories.abc_async_generic_repository import \
    ABCAsyncGenericRepository


class ABCAsyncApiKeyRepository(
    ABCAsyncGenericRepository[ApiKey],
    metaclass=ABCMeta,
):
    ...
