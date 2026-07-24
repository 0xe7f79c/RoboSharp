from typing import TYPE_CHECKING, Optional

import asyncpg
import discord
from discord.app_commands import AppCommandError
from discord.ext import commands

from cogs.utils.context import GuildContext

if TYPE_CHECKING:
    from ..bot import RSharp


class AdminError(ValueError, AppCommandError):
    pass


class Admin(commands.Cog):
    """Moderation tools for your discord server."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot
        self.pool = self.bot.pool

    async def cog_command_error(self, ctx, error):
        if isinstance(error, Exception):
            error = error.original
            if isinstance(error, AdminError):
                await ctx.send(str(error))

    async def get_default_role(self, guild_id: int) -> Optional[discord.Role]:
        """Returns the Guilds default role."""
        async with self.pool.acquire() as conn:
            query = """SELECT RoleId FROM DefaultRole WHERE GuildId = $1"""
            record: asyncpg.Record = await conn.fetchrow(query, guild_id)

            if record is None:
                return None

            role_id: int = record[0]
            guild = self.bot.get_guild(guild_id)
            role = guild.get_role(role_id)

            if role is None:
                return None

            return role

    @commands.hybrid_group()
    async def admin(self, ctx: GuildContext):
        raise AdminError('Todo')


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Admin(bot=bot))
