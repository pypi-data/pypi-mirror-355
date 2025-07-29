from typing import TypeVar

from ed_domain.core.aggregate_roots import Order

from ed_optimization.application.contracts.infrastructure.cache.abc_cache import \
    ABCCache

T = TypeVar("T")


class InMemoryCache(ABCCache[list[Order]]):
    def __init__(self) -> None:
        self._cache: dict[str, list[Order]] = {}

    async def get(self, key: str) -> list[Order] | None:
        return self._cache.get(key)

    async def set(self, key: str, value: list[Order]) -> None:
        self._cache[key] = value
