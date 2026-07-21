from typing import TYPE_CHECKING, Optional, TypeVar, Union

import asyncpg
import discord
from discord.abc import GuildChannel
from discord.app_commands import AppCommandError
from discord.channel import TextChannel, VocalGuildChannel
from discord.ext import commands

from cogs.utils.context import GuildContext

if TYPE_CHECKING:
    from ..bot import RSharp

    GemChannel = TypeVar('GemChannel', bound=Union[TextChannel, VocalGuildChannel])


class GemError(ValueError, AppCommandError):
    pass


class GuildGemboard:
    def __init__(self, bot: RSharp, record: asyncpg.Record) -> None:
        self.bot = bot
        if record is not None:
            self.guild_id: int = record['guild_id']
            self.channel_id: int = record['channel_id']
            self.requirement: int = record['threshold']
            self.locked: bool = record['locked']

            channel: GuildChannel = self.bot.get_channel(self.channel_id)
            if isinstance(channel, GemChannel):
                self.channel: GemChannel = channel
            else:
                self.channel = None
        else:
            raise GemError('\N{BLACK QUESTION MARK ORNAMENT} This server does not have a starboard.')

    def get_guild(self) -> discord.Guild:
        guild: discord.Guild = self.bot.get_guild(self.guild_id)
        return guild


class GemContext(GuildContext):
    gemboard: GuildGemboard


def requires_gemboard() -> any:
    async def wrapper(ctx: GemContext) -> bool:
        guild = ctx.guild
        if guild is None:
            await ctx.send('\N{NO ENTRY} You cannot run this command in DMs.')
            return False

        gem_cog: Gems = ctx.bot.get_cog('Gems')
        gemboard = await gem_cog._get_gemboard(guild.id)
        if gemboard is None:
            await ctx.send('\N{NO ENTRY SIGN} This server does not have a Gemboard.')
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
        else:
            await ctx.send(str(error))

    async def get_gemboard(self, guild_id: int) -> Optional[GuildGemboard]:
        async with self.pool.acquire() as conn:
            query = """SELECT * FROM gemboard WHERE guild_id = $1"""
            record: asyncpg.Record = await conn.fetchrow(query, guild_id)
            if record is None:
                return None
            gemboard: GuildGemboard = GuildGemboard(self.bot, record)
            return gemboard

    async def _create_gemboard(self, guild_id: discord.Guild, channel_id: int, threshold: int) -> None:
        pass

    @commands.hybrid_group()
    async def gems(self, ctx: GemContext) -> None:
        """View your current gemboard stats. (If any)"""
        gemguild = ctx.gemboard.channel
        if gemguild is None:
            await ctx.send('\N{WHITE QUESTION MARK ORNAMENT} This server does not have a Gemboard.')
            return
        await ctx.send(f'Gemboard located at: {gemguild}')

    @gems.command()
    @commands.has_permissions(manage_channels=True)
    async def create(self, ctx: GuildContext, name: str = 'gemboard', *, threshold: int = 3) -> None:
        gemboard = await self.get_gemboard(ctx.guild.id)
        deleted = False
        if gemboard is not None:
            # check if the channel itself exists
            channel = gemboard.channel
            if channel is not None:
                await ctx.send(f'Apparently, you already have a Gemboard set up: {channel.mention}...')
                return
            # it was deleted then, probably
            deleted = True
        try:
            if deleted:
                await ctx.send("It appears the old channel was deleted. Would you like to recognize already gem'd entries?")
            await ctx.send('meow')
        except discord.Forbidden:
            await ctx.send('\N{NO ENTRY SIGN} I cannot create channels.')
            return
        except discord.NotFound:
            await ctx.send(
                '\N{NO ENTRY} Something went wrong when accessing the Gemboard channel. (Perhaps it was deleted mid-way?)'
            )
            return
        except GemError:
            return
        except Exception:
            await ctx.send('Something went wrong.')
            return


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Gems(bot=bot))
