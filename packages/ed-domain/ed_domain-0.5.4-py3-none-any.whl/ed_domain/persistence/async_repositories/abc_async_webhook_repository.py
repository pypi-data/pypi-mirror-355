from abc import ABCMeta

from ed_domain.core.entities.webhook import Webhook
from ed_domain.persistence.async_repositories.abc_async_generic_repository import \
    ABCAsyncGenericRepository


class ABCAsyncWebhookRepository(
    ABCAsyncGenericRepository[Webhook],
    metaclass=ABCMeta,
):
    ...
