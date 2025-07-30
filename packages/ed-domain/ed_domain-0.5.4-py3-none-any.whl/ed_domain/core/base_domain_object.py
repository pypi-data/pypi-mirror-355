from dataclasses import dataclass
from uuid import UUID


@dataclass
class BaseDomainObject:
    id: UUID

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
