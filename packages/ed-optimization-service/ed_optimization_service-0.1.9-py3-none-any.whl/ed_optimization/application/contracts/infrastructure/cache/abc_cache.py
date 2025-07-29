from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class ABCCache(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    async def get(self, key: str) -> T | None: ...

    @abstractmethod
    async def set(self, key: str, value: T) -> None: ...
