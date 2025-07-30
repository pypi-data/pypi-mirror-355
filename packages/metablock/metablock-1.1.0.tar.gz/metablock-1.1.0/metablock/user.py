from typing import Any

from .components import MetablockEntity, MetablockResponseError
from .orgs import Org, Orgs


class User(MetablockEntity):
    """Object representing a Metablock user"""

    @property
    def url(self) -> str:
        return f"{self.root.url}/user"

    async def orgs(self, **kwargs: Any) -> list[Org]:
        """List user organizations"""
        orgs = Orgs(self.root, Org)
        kwargs.setdefault("wrap", lambda dl: [Org(orgs, d) for d in dl])
        return await self.cli.get(f"{self.url}/orgs", **kwargs)

    async def get_permissions(self, **kwargs: Any) -> list[dict]:
        """List user permissions"""
        return await self.cli.get(f"{self.url}/permissions", **kwargs)

    async def tokens(self, **kwargs: Any) -> list[dict]:
        return await self.cli.get(f"{self.url}/tokens", **kwargs)

    async def create_token(self, **kwargs: Any) -> dict:
        return await self.cli.post(f"{self.url}/tokens", **kwargs)

    async def delete_token(self, token_id: str, **kwargs: Any) -> dict:
        return await self.cli.delete(f"{self.url}/tokens/{token_id}", **kwargs)

    async def check_password(self, password: str, **kwargs: Any) -> bool:
        try:
            return await self.cli.post(
                f"{self.url}/password", json=dict(password=password), **kwargs
            )
        except MetablockResponseError as exc:
            if exc.status == 401:
                return False
            else:
                raise
