import asyncio
import uuid
from typing import TYPE_CHECKING, Optional

import asyncpg
import discord
from discord.app_commands import AppCommandError
from discord.ext import commands

from cogs.utils.context import GuildContext

if TYPE_CHECKING:
    from ..bot import RSharp


class GemfulGuild:
    def __init__(self, bot: RSharp, guild_id: int, record: asyncpg.Record):
        self.bot = bot
        self.guild_id = guild_id
        if record is not None:
            self.channel_id: int = record['ChannelId']
            self.threshold: int = record['Threshold']
            self.locked: bool = record['Locked']
            self.sku: uuid.UUID = record['SKU']
            self.created_on = record['CreatedOn']
            self.track_previous: bool = record['TrackPrevious']
        else:
            self.channel_id = None

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        channel: discord.TextChannel = self.bot.get_channel(self.channel_id)
        return channel


class GemContext(GuildContext):
    gemboard: GemfulGuild


class GemError(ValueError, AppCommandError):
    pass


def require_gemboard():
    async def wrapper(ctx: GemContext) -> bool:
        if ctx.guild is None:
            return False
        guild_id: int = ctx.guild.id
        gem_cog: Gems = ctx.bot.get_cog('Gems')

        gemboard = await gem_cog.get_gemboard(guild_id)
        if gemboard.channel is None:
            raise GemError('This server does not have a Gemboard.')

        ctx.gemboard = gemboard
        return True

    return commands.check(wrapper)


class Gems(commands.Cog):
    def __init__(self, bot: RSharp):
        self.bot = bot
        self.pool = bot.pool

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.HybridCommandError):
            error = error.original
        if isinstance(error, GemError):
            await ctx.send(str(error))

    async def get_gemboard(self, guild_id: int) -> Optional[GemfulGuild]:
        async with self.pool.acquire() as connection:
            query = """
            SELECT
                SKU as "SKU", 
                ChannelId as "ChannelId",
                Locked as "Locked",
                TrackPrevious as "TrackPrevious",
                Threshold as "Threshold",
                CreatedOn as "CreatedOn"
            FROM Gems WHERE GuildId = $1"""
            row: asyncpg.Record = await connection.fetchrow(query, guild_id)
            config = GemfulGuild(bot=self.bot, guild_id=guild_id, record=row)
            return config

    async def toggle_gem_lock(self, guild_id: int, gemboard: GemfulGuild) -> bool:
        lock = True

        if gemboard.channel is None:
            raise GemError('\N{NO ENTRY SIGN} The Gemboard for this server does not exist.')
        if gemboard.locked:
            lock = False

        async with self.pool.acquire() as connection:
            query = """UPDATE Gems
                       SET Locked=$1
                       WHERE GuildId=$2
            """

            await connection.execute(query, lock, guild_id)
            gemboard.locked = lock

    async def create_server_gemboard(self, guild_id: int, channel_id: int, threshold: int) -> GemfulGuild:
        pass

    @commands.hybrid_group(guild=discord.Object(id=678655372197625858), fallback='create')
    @commands.has_permissions(manage_guild=True)
    async def gems(self, ctx: GuildContext, category: discord.CategoryChannel, channel_name: str):
        """Creates a Gemboard for the server if one doesnt exist.
        Args:
            channel_name (str): The name of the Gemboard channel.
            category (str, optional): The Category to place the channel under.
        """
        await ctx.defer()
        gemboard = await self.get_gemboard(ctx.guild.id)
        if hasattr(gemboard, 'locked'):
            if gemboard.channel is not None:
                await ctx.send(f'Apparently, you already have a Gemboard: {gemboard.channel.mention}')
                return
            view_result = await ctx.confirm(
                'It appears that the original Gemboard (#no-access) was deleted/hidden. Would you like to start over?'
            )
            if view_result is None:
                raise GemError('\N{WHITE QUESTION MARK ORNAMENT} Timed out. You took too long.', ephemeral=True)
            if view_result is False:
                raise GemError('Aborted Gemboard creation.')
            connection = self.bot.pool
            query = """DELETE FROM Gems WHERE GuildID = $1"""
            await connection.execute(query, ctx.guild.id)
        try:
            default_role = await ctx.default_role()

            overwrites = {
                ctx.me: discord.PermissionOverwrite(
                    view_channel=True, manage_messages=True, send_messages=True, read_messages=True, pin_messages=True
                ),
                default_role: discord.PermissionOverwrite(
                    view_channel=True, manage_messages=False, send_messages=False, pin_messages=False
                ),
            }

            username = ctx.author.name
            user_id = ctx.author.id
            try:
                channel = await ctx.guild.create_text_channel(
                    channel_name,
                    reason=f'Gemboard created by {username}. (ID: {user_id})',
                    overwrites=overwrites,
                    category=category,
                )
                try:
                    query = """INSERT INTO Gems (GuildId, ChannelId) VALUES ($1, $2)"""
                    await self.pool.execute(query, ctx.guild.id, channel.id)
                    await ctx.reply(f'\N{GEM STONE} Gemboard created: {channel.mention}')
                except Exception:
                    await ctx.send('The channel could not be created due to an internal issue.', ephemeral=True)
                    await channel.delete()
                    return
            except discord.Forbidden:
                await ctx.send('\N{NO ENTRY SIGN} Could not create channel due to low permissions.', ephemeral=True)
                return
        except discord.Forbidden:
            await ctx.send(
                '\N{NO ENTRY SIGN} Could not change permissions due to me having low permissions myself.`', ephemeral=True
            )
            return
        except GemError:
            return
        except asyncio.TimeoutError:
            await ctx.send('You took too long. Aborting...', ephemeral=True)
            return
        except Exception as ex:
            print(ex)
            await ctx.send('\N{WHITE QUESTION MARK ORNAMENT} An unknown error occured.')

    @gems.command()
    @require_gemboard()
    async def lock(self, ctx: GemContext) -> None:
        """
        Toggles the servers Gemboard lock, which effects \N{GEM STONE} reactions.
        """
        await ctx.defer()
        gemboard = ctx.gemboard
        await self.toggle_gem_lock(ctx.guild.id, gemboard)
        channel = gemboard.channel

        if gemboard.locked:
            await ctx.reply(f"\N{LOCK} {channel.mention} is locked and will **no longer** recieve newly made \N{GEM STONE}'s.")
        else:
            await ctx.reply(f"\N{OPEN LOCK} {channel.mention} is now unlocked and **will** recieve newly made \N{GEM STONE}'s.")

    @gems.group(name='threshold', fallback='view')
    @require_gemboard()
    async def _threshold(self, ctx: GemContext):
        """Commands to change how many \N{GEM STONE}'s a message will need."""
        await ctx.defer()
        threshold = ctx.gemboard.threshold
        await ctx.reply(f"A message currently requires: {threshold} `\N{GEM STONE}`'s before it can be posted in the Gemboard.")

    @_threshold.command()
    @require_gemboard()
    async def change(self, ctx: GemContext, threshold: int = 3):
        """
        Changes the requirement to post on the servers Gemboard.

        Parameters
        ----------
        threshold: int
            The new threshold requirement to post on the Gemboard.
        """
        await ctx.defer()
        if threshold <= 0:
            raise GemError('\N{CROSS MARK} Threshold must be greater than zero.')
        gemboard = ctx.gemboard
        async with self.pool.acquire() as connection:
            query = """UPDATE Gems SET Threshold = $1 WHERE GuildId = $2"""
            await connection.execute(query, threshold, ctx.guild.id)

        gemboard.threshold = threshold
        await ctx.reply(f'\N{WHITE HEAVY CHECK MARK} Changed Gemboard threshold to: `{threshold}`.')


async def setup(bot: RSharp):
    await bot.add_cog(Gems(bot=bot))
