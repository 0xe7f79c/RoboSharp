from typing import Any, Dict

import asyncpg
from discord import Guild
from discord.ext import commands


class RContext(commands.Context):
    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        super().__init__(**kwargs)


class GuildContext(RContext):
    guild: Guild
    pool: asyncpg.Pool
