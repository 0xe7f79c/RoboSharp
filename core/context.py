from typing import Any

import asyncpg
from discord import Guild
from discord.ext import commands

__all__ = ('RContext', 'GuildContext')


class RContext(commands.Context):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        super().__init__(**kwargs)


class GuildContext(RContext):
    guild: Guild
    pool: asyncpg.Pool
