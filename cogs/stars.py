from typing import TYPE_CHECKING

import asyncpg
from discord.abc import GuildChannel
from discord.app_commands import AppCommandError
from discord.ext import commands

from cogs.utils.context import GuildContext

if TYPE_CHECKING:
    from ..bot import RSharp


class GemError(ValueError, AppCommandError):
    pass


class GuildGemboard:
    def __init__(self, bot: RSharp, record: asyncpg.Record) -> None:
        self.bot = bot
        if record is not None:
            self.guild_id: int = record['guildid']
            self.channel_id: int = record['channel']
            self.requirement: int = record['requirement']
            self.locked: bool = record['locked']
        else:
            raise GemError('This server does not have a gemboard!')

    def get_channel(self) -> GuildChannel:
        channel: GuildChannel = self.bot.get_channel(self.channel_id)
        return channel


class GemContext(GuildContext):
    gemboard: GuildGemboard


def requires_gemboard() -> any:
    async def wrapper(ctx: GemContext) -> bool:
        guild = ctx.guild

        if guild is None:
            return False

        gem_cog: Gems = await ctx.bot.get_cog('Gems')
        gemboard = await gem_cog.get_gemboard(guild.id)

        if gemboard is None:
            return False

        ctx.gemboard = gemboard
        return True

    return commands.check(wrapper)


class Gems(commands.Cog):
    """A feature to upvote posts."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot
        self.pool: asyncpg.Pool = bot.pool

    async def cog_command_error(self, ctx: GemContext, error: Exception) -> None:
        if isinstance(error, Exception):
            error = error.original
            if isinstance(error, GemError):
                await ctx.send(str(error))

    async def get_gemboard(self, guild_id: int) -> GuildGemboard:
        async with self.pool.acquire() as conn:
            query: str = """SELECT * FROM gemboards WHERE guildid = $1"""
            record: asyncpg.Record = conn.fetchrow(query, guild_id)
            return GuildGemboard(self.bot, record)

    @commands.hybrid_group()
    @requires_gemboard()
    async def gems(self, ctx: GemContext) -> None:
        """View your current gemboard stats. (If any)"""
        await ctx.send('placeholder')


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Gems(bot=bot))
