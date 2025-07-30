from abc import abstractmethod
from typing import Generic, Optional, TypeVar
from uuid import UUID

from ed_domain.common.logging import get_logger
from ed_domain.persistence.async_repositories.abc_async_car_repository import \
    ABCAsyncGenericRepository

LOG = get_logger()
TCreateDto = TypeVar("TCreateDto")
TUpdateDto = TypeVar("TUpdateDto")
TDto = TypeVar("TDto")
TEntity = TypeVar("TEntity")


class ABCService(Generic[TEntity, TCreateDto, TUpdateDto, TDto]):
    def __init__(self, name: str, repository: ABCAsyncGenericRepository) -> None:
        self._name = name
        self._repository = repository

    @abstractmethod
    async def create(self, dto: TCreateDto) -> TEntity: ...

    @abstractmethod
    async def update(self, id: UUID, dto: TUpdateDto) -> Optional[TEntity]: ...

    async def get(self, id: UUID) -> Optional[TEntity]:
        entity = await self._repository.get(id=id)
        if entity:
            LOG.info(f"{self._name} found for ID: {id}")
        else:
            LOG.info(f"No {self._name.lower()} found for ID: {id}")
        return entity

    async def get_all(self) -> list[TEntity]:
        entities = await self._repository.get_all()
        LOG.info(f"Retrieving all {len(entities)} {self._name.lower()}s.")
        return entities

    async def delete(self, id: UUID) -> bool:
        deleted = await self._repository.delete(id)
        if deleted:
            LOG.info(f"{self._name} with ID: {id} deleted.")
            return True
        else:
            LOG.error(
                f"Cannot delete: No {self._name.lower()} found for ID: {id}")
            return False

    async def save(self, entity: TEntity) -> TEntity:
        return await self._repository.save(entity)

    @abstractmethod
    async def to_dto(self, entity: TEntity) -> TDto: ...
