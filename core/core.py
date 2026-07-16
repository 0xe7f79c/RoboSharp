import asyncpg
from discord import Guild
from discord.ext import commands


class RContext(commands.Context):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class GuildContext(RContext):
    guild: Guild
    pool: asyncpg.Pool
