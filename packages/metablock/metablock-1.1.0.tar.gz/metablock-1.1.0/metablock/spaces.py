from __future__ import annotations

from pathlib import Path
from typing import Any

from .components import Component, CrudComponent, MetablockEntity


# Space
class Space(MetablockEntity):
    """Object representing a space"""

    @property
    def blocks(self) -> SpaceBlocks:
        return SpaceBlocks(self, Block, "blocks")

    @property
    def extensions(self) -> SpaceExtensions:
        return SpaceExtensions(self, SpaceExtension, "extensions")


class Spaces(CrudComponent[Space]):
    """Spaces"""


# Service
class Block(MetablockEntity):
    """Object representing a block in a space"""

    @property
    def plugins(self) -> BlockPlugins:
        return BlockPlugins(self, BlockPlugin, "plugins")

    @property
    def deployments(self) -> Deployments:
        return Deployments(self, Deployment, "deployments")

    async def config(self, *, callback: Any = None) -> dict:
        return await self.cli.get(f"{self.url}/config", callback=callback)

    async def certificate(self, *, callback: Any = None) -> dict:
        return await self.cli.get(f"{self.url}/certificate", callback=callback)

    async def ship(
        self,
        bundle_path: str | Path,
        name: str = "",
        env: str = "stage",
        **kwargs: Any,
    ) -> dict:
        p = Path(bundle_path)
        return await self.cli.post(
            f"{self.url}/deployments",
            data=dict(name=name, env=env),
            files=dict(bundle=(p.name, p.read_bytes())),
            **kwargs,
        )

    async def add_route(self, *, callback: Any = None, **kwargs: Any) -> dict:
        """Add a new route to the block"""
        return await self.cli.post(f"{self.url}/routes", json=kwargs, callback=callback)

    async def update_route(
        self, name: str, *, callback: Any = None, **kwargs: Any
    ) -> dict:
        """Update a route in the block"""
        return await self.cli.patch(
            f"{self.url}/routes/{name}", json=kwargs, callback=callback
        )


# For backward compatibility
Service = Block


class Blocks(CrudComponent[Block]):
    """Blocks"""


class SpaceBlocks(Blocks):
    def list_create_url(self) -> str:
        return "%s/%s" % (self.root.url, self.name)


# SpaceExtension
class SpaceExtension(MetablockEntity):
    """Object representing an SpaceExtension"""


class SpaceExtensions(CrudComponent[SpaceExtension]):
    def list_create_url(self) -> str:
        return "%s/%s" % (self.root.url, self.name)

    def delete_url(self, id_name: str) -> str:
        return f"{self.parent_url}/{id_name}"


# ServicePlugin


class BlockPlugin(MetablockEntity):
    """Object representing an ServicePlugin"""


class BlockPlugins(CrudComponent[BlockPlugin]):
    def list_create_url(self) -> str:
        return "%s/%s" % (self.root.url, self.name)


# Deployment


class Deployment(MetablockEntity):
    """Object representing a deployment"""


class Deployments(CrudComponent[Deployment]):
    """deployments"""


# Domain


class Domains(Component):
    async def check(self, domain: str) -> str:
        return await self.cli.get(f"{self.url}/check/{domain}")
