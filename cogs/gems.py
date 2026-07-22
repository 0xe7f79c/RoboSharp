from typing import TYPE_CHECKING, Optional, Union

import asyncpg
import discord
from discord.app_commands import AppCommandError
from discord.channel import TextChannel, VocalGuildChannel
from discord.ext import commands

from cogs.admin import Admin
from cogs.utils.context import GuildContext

if TYPE_CHECKING:
    from ..bot import RSharp

GemChannel = Union[TextChannel, VocalGuildChannel]


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
            self._channel = self.bot.get_channel(self.channel_id)
        else:
            raise GemError('\N{BLACK QUESTION MARK ORNAMENT} This server does not have a starboard.')

    @property
    def channel(self) -> GemChannel:
        return self._channel

    def get_guild(self) -> discord.Guild:
        guild: discord.Guild = self.bot.get_guild(self.guild_id)
        return guild


class GemContext(GuildContext):
    gemboard: GuildGemboard


def requires_gemboard():
    async def wrapper(ctx: GemContext) -> bool:
        guild = ctx.guild
        if guild is None:
            await ctx.send('\N{NO ENTRY} You cannot run this command in DMs.')
            return False
        bot: RSharp = ctx.bot
        gem_cog: Gems = bot.get_cog('Gems')

        gemboard: GuildGemboard = await gem_cog.get_gemboard(guild.id)
        if gemboard is None:
            await ctx.send('\N{NO ENTRY SIGN} This server does not have a Gemboard.')
            return False

        # it might be deleted
        if gemboard.channel is None:
            await ctx.send('\N{NO ENTRY SIGN} This server does not have a Gemboard. (Perhaps it was deleted?)')
            return False

        ctx.gemboard = gemboard
        return True

    return commands.check(wrapper)


class Gems(commands.Cog):
    """A feature to upvote posts."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot
        self.pool: asyncpg.Pool = bot.pool

    async def cog_command_error(self, ctx: GemContext, error):
        if isinstance(error, Exception):
            error = error.original
            if isinstance(error, GemError):
                await ctx.send(str(error))

    async def get_gemboard(self, guild_id: int) -> Optional[GuildGemboard]:
        async with self.pool.acquire() as conn:
            query = """SELECT * FROM gemboard WHERE guild_id = $1"""
            record: asyncpg.Record = await conn.fetchrow(query, guild_id)
            if record is None:
                return None

            gemboard: GuildGemboard = GuildGemboard(self.bot, record)
            return gemboard

    async def _wipe_gemboard(self, guild_id: int) -> None:
        async with self.pool.acquire() as conn:
            query = """DELETE FROM gemboard WHERE guild_id = $1"""
            await conn.execute(query, guild_id)

    async def _create_gemboard(self, guild_id: int, channel_id: int, threshold: int) -> None:
        async with self.pool.acquire() as conn:
            query = """INSERT INTO gemboard (guild_id, channel_id, threshold)
                       VALUES($1, $2, $3)"""
            await conn.execute(query, guild_id, channel_id, threshold)

    @commands.hybrid_group()
    async def gems(self, ctx: GuildContext, name: str = 'gemboard', *, threshold: int = 3) -> None:
        """Creates a new gemboard, and replenishes one if it was deleted."""
        guild = ctx.guild
        gemboard = await self.get_gemboard(guild.id)
        if gemboard is not None:
            # check if the channel itself exists
            channel = gemboard.channel
            if channel is not None:
                await ctx.send(f'Apparently, you already have a Gemboard set up: {channel.mention}...')
                return

            confirm = await ctx.prompt(
                'Apparently, you already had a Gemboard set up but it was deleted. Would you like to start over? [y/n]'
            )
            if confirm:
                await self._wipe_gemboard(guild.id)
            else:
                await ctx.send('An unknown issue occured.')
                return
        try:
            # find the default role to target the overwrite towards
            admin_cog: Admin = self.bot.get_cog('Admin')
            default_role = await admin_cog.get_default_role(guild.id)
            if default_role is None:
                # no custom default role set for the guild
                default_role = guild.default_role

            overwrites = {
                ctx.me: discord.PermissionOverwrite(manage_messages=True, send_messages=True, view_channel=True),
                default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=False,
                    read_messages=True,
                    add_reactions=True,
                ),
            }

            user_id = ctx.author.id
            username = ctx.author.name
            channel = await guild.create_text_channel(
                name=name,
                reason=f'\N{GEM STONE} Gemboard created by: {username} (User ID: {user_id})',
                overwrites=overwrites,
            )
            await ctx.send(f'Gemboard created: {channel.mention}')
            await self._create_gemboard(guild_id=guild.id, channel_id=channel.id, threshold=threshold)
        except discord.Forbidden:
            await ctx.send('\N{NO ENTRY SIGN} Aborted Gemboard creation: I cannot access this channel.')
            return
        except discord.NotFound:
            await ctx.send(
                '\N{NO ENTRY} Aborted Gemboard creation:'
                + ' Something went wrong when accessing the Gemboard channel. (Perhaps it was deleted mid-way?)'
            )
            return
        except GemError:
            return
        except Exception:
            await ctx.send('Something went wrong.')
            return


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Gems(bot=bot))
