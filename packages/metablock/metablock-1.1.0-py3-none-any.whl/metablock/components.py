from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Mapping,
    TypeVar,
    cast,
)

from httpx import Response as ClientResponse

from .utils import as_dict, as_params

if TYPE_CHECKING:  # pragma: no cover
    from .client import Metablock


Callback = Callable[[ClientResponse], Awaitable[Any]]


class MetablockError(Exception):
    pass


class MetablockResponseError(MetablockError):
    def __init__(self, response: ClientResponse, message: Any = "") -> None:
        self.response = response
        self.message = as_dict(message, "message")
        self.message["request_url"] = str(response.url)
        self.message["request_method"] = response.request.method
        self.message["response_status"] = response.status_code

    @property
    def status(self) -> int:
        return self.response.status_code

    def __str__(self) -> str:
        return json.dumps(self.message, indent=4)


class HttpComponent(ABC):
    @property
    @abstractmethod
    def cli(self) -> Metablock:  # pragma: no cover
        ...

    @property
    @abstractmethod
    def url(self) -> str:  # pragma: no cover
        ...

    def __repr__(self) -> str:
        return self.url

    def __str__(self) -> str:
        return self.__repr__()


class Component(HttpComponent):
    def __init__(
        self, root: Metablock | CrudComponent | MetablockEntity, name: str = ""
    ) -> None:
        self.root = root
        self.name = name or self.__class__.__name__.lower()

    @property
    def cli(self) -> Metablock:
        return self.root.cli

    @property
    def url(self) -> str:
        return f"{self.cli.url}/{self.name}"

    @property
    def parent_url(self) -> str:
        return f"{self.root.url}/{self.name}"

    @property
    def is_entity(self) -> bool:
        return isinstance(self.root, MetablockEntity)


class MetablockEntity(HttpComponent):
    """A Metablock entity"""

    __slots__ = ("root", "data")

    def __init__(
        self,
        root: Metablock | CrudComponent | MetablockEntity,
        data: dict,
    ) -> None:
        self.root = root
        self.data = data

    def __repr__(self) -> str:
        return repr(self.data)

    def __getitem__(self, item: str) -> Any:
        return self.data[item]

    def __contains__(self, item: str) -> bool:
        return item in self.data

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.data == other.data

    def _asdict(self) -> dict:
        return self.data

    @property
    def cli(self) -> Metablock:
        return self.root.cli

    @property
    def id(self) -> str:
        return self.data.get("id", "")

    @property
    def name(self) -> str:
        return self.data.get("name", "")

    @property
    def url(self) -> str:
        return "%s/%s" % (self.root.url, self.id)

    def nice(self) -> str:
        return json.dumps(self.data, indent=4)


E = TypeVar("E", bound="MetablockEntity")


class CrudComponent(Component, Generic[E]):
    def __init__(
        self,
        root: Metablock | CrudComponent | MetablockEntity,
        factory: type[E],
        name: str = "",
    ) -> None:
        super().__init__(root, name)
        self.factory = factory

    async def paginate(self, **params: Any) -> AsyncIterator[E]:
        next_ = self.list_create_url()
        url_params: Any = as_params(**params)
        while next_:
            next_, data = await self.cli.request(
                next_, params=url_params, callback=self._paginated
            )
            url_params = None
            for d in data:
                yield self.entity(d)

    async def get_list(self, **kwargs: Any) -> list[E]:
        url = self.list_create_url()
        kwargs.setdefault("wrap", self.entity_list)
        return cast(
            list[E],
            await self.cli.request(url, **kwargs),
        )

    async def get_full_list(self, **kwargs: Any) -> list[E]:
        return [d async for d in self.paginate(**kwargs)]

    async def get(self, id_: str, **kwargs: Any) -> E:
        url = f"{self.url}/{id_}"
        kwargs.setdefault("wrap", self.entity)
        return cast(E, await self.cli.get(url, **kwargs))

    async def has(self, id_: str, **kwargs: Any) -> bool:
        url = f"{self.url}/{id_}"
        return cast(bool, await self.cli.get(url, callback=self._head))

    async def create(self, callback: Callback | None = None, **params: Any) -> E:
        url = self.list_create_url()
        return cast(
            E,
            await self.cli.post(url, json=params, callback=callback, wrap=self.entity),
        )

    async def update(
        self, id_name: str, callback: Callback | None = None, **params: Any
    ) -> E:
        return cast(
            E,
            await self.cli.patch(
                self.update_url(id_name),
                json=params,
                callback=callback,
                wrap=self.entity,
            ),
        )

    async def upsert(self, callback: Callback | None = None, **params: Any) -> E:
        return cast(
            E,
            await self.cli.put(
                self.url, json=params, callback=callback, wrap=self.entity
            ),
        )

    async def delete(  # type: ignore
        self,
        id_name: str,
        **kwargs: Any,
    ) -> Any:
        return await self.cli.delete(self.delete_url(id_name), **kwargs)

    async def delete_all(self) -> int:
        n = 0
        async for entity in self.paginate():
            await self.delete(entity.id)
            n += 1
        return n

    def entity(self, data: dict) -> E:
        return self.factory(self, data)

    def entity_list(self, data: list[dict]) -> list[E]:
        return [self.entity(d) for d in data]

    def list_create_url(self) -> str:
        return self.parent_url if self.is_entity else self.url

    def update_url(self, id_name: str) -> str:
        return f"{self.url}/{id_name}"

    def delete_url(self, id_name: str) -> str:
        return f"{self.url}/{id_name}"

    # callbacks

    async def _head(self, response: ClientResponse) -> bool:
        if response.status_code == 404:
            return False
        elif response.status_code == 200:
            return True
        else:  # pragma: no cover
            raise MetablockResponseError(response)

    async def _paginated(self, response: ClientResponse) -> Any:
        next_ = response.links.get("next")
        if isinstance(next_, Mapping):
            url = next_.get("url")
        else:
            url = None
        data = await self.cli.handle_response(response)
        return (url, data)
