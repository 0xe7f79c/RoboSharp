import asyncio
from typing import Dict, Optional, Tuple

import asyncpg
import discord
from discord.app_commands import AppCommandError
from discord.ext import commands, tasks
from discord.ext.commands._types import Check

from bot import RSharp
from cogs.utils.context import GuildContext


class ValidStarChannel(discord.TextChannel):
    pass


MAX_FIELD_LEN = 120
ALLOWED_MIMES = ['image/jpeg', 'image/webp', 'image/png', 'image/gif']


class GuildStarboard:
    def __init__(self, bot: RSharp, guild_id: int, record: asyncpg.Record) -> None:
        self.bot = bot
        self.guild_id = guild_id

        if record is not None:
            self.channel_id = record['channel_id']
            self.post_requirement = record['post_requirement']
            self.created_on = record['created_on']
            self.locked = record['locked']
        else:
            self.channel_id = None

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        channel = self.bot.get_channel(self.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return None
        return channel


class StarContext(GuildContext):
    starboard: GuildStarboard


def starboard_only() -> Check[StarContext]:
    async def wrapper(ctx: StarContext) -> bool:
        if ctx.guild is None:
            return False

        guild_id = ctx.guild.id
        star_cog: Starboard = ctx.bot.get_cog('Starboard')
        starboard = await star_cog.get_starboard(guild_id)

        if starboard.channel is None:
            return False

        ctx.starboard = starboard
        return True

    return commands.check(wrapper)


class StarboardError(ValueError, AppCommandError):
    pass


class Starboard(commands.Cog):
    """Dynamically updating pins for your server."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot
        self.pool = bot.pool

        self.message_cache: Dict[int, discord.Message] = {}
        self.clear_message_cache_loop.start()

    async def cog_command_error(self, ctx, error) -> None:
        if isinstance(error, commands.HybridCommandError):
            error = error.original
        if isinstance(error, StarboardError):
            await ctx.send(str(error))

    @tasks.loop(hours=1, count=None)
    async def clear_message_cache_loop(self) -> None:
        self.message_cache.clear()

    async def get_starboard(self, guild_id: int) -> GuildStarboard:
        query = """SELECT
                    channel_id AS "channel_id",
                    post_requirement AS "post_requirement",
                    created_on AS "created_on",
                    locked AS "locked"
                FROM Starboards WHERE guild_id=$1"""
        record = await self.pool.fetchrow(query, guild_id)
        return GuildStarboard(self.bot, guild_id, record)

    def get_emoji(self, stars: int) -> str:
        if 0 <= stars < 3:
            return '\N{WHITE MEDIUM STAR}'
        elif 3 <= stars < 6:
            return '\N{GLOWING STAR}'
        elif 6 <= stars < 9:
            return '\N{DIZZY SYMBOL}'

        return '\N{SPARKLES}'

    def get_color_brightness(self, stars: int) -> discord.Color:
        r_min = 0
        r_max = 10

        if stars < r_min:
            stars = r_min
        elif stars > r_max:
            stars = r_max

        max_b = 255
        min_b = 0  # highest brightness
        blue = max_b - (max_b - min_b) * (stars - r_min) / (r_max - r_min)
        red = 255
        green = 255

        return discord.Color.from_rgb(int(red), int(green), int(blue))

    async def get_message(self, channel_id: int, message_id: int) -> Optional[discord.Message]:
        """Finds a message in the bots internal cache.

        Args
        ----
            channel_id (int): The channel ID of where the message lives.
            message_id (int): The message id of the message.

        Returns
        -------
            Optional[discord.Message]: The cached message object. None if the message was deleted.

        Raises
        -------
            discord.Forbidden
                If the resource was behind a permission the bot doesn't possess.
            discord.InvalidData
                An unknown channel type was received from Discord.
            HTTPException
                Retrieving the channel failed.
        """

        try:
            if message_id in self.message_cache:
                msg = self.message_cache[message_id]
                return msg

            channel = await self.bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)

            self.message_cache[message_id] = message
            return message
        except discord.NotFound:
            return None

    async def create_star_message(self, message: discord.Message, stars: int, time) -> Tuple[str, discord.Embed, discord.ui.View]:
        """Creates components for Starboard posts.

        Args:
            message (discord.Message): The message that was starred.
            stars (int): How many stars the message obtained.
            time (datetime, optional): The time this interaction was registered.
        Returns:
            Tuple[str, discord.Embed, discord.ui.View]: The individual parts of the post as a tuple. First being the heading,
            second being the embed, and the third being the view containing the jump button.
        """

        embed_col = self.get_color_brightness(stars)
        embed = discord.Embed(color=embed_col)

        display_emoji = self.get_emoji(stars)
        heading = f'{display_emoji} {stars} | {message.channel.mention}'

        author_name = message.author.name
        author_icon = message.author.avatar
        embed.set_author(name=author_name, icon_url=author_icon.url)

        content = message.clean_content
        if len(content) > MAX_FIELD_LEN:
            content = f'{content[0:MAX_FIELD_LEN]}'
            content += f'[...]({message.jump_url})'

        original_attachments = message.attachments
        if len(original_attachments) > 0:
            attachment = original_attachments[0]
            if attachment.content_type in ALLOWED_MIMES:
                embed.set_image(url=attachment.url)
            else:
                embed.add_field(name='File', value=f'[View file]({attachment.url})', inline=False)

        embed.add_field(name='Message', value=content)

        has_reply_content = True if message.reference is not None else False
        if has_reply_content:
            resolved = message.reference.resolved
            who = resolved.author
            name = who.name

            content = resolved.clean_content
            if len(content) > MAX_FIELD_LEN:
                content = content[0:MAX_FIELD_LEN]
                content += f'[...]({resolved.jump_url})'

            embed.add_field(name=f'Replying to {name}', value=f'> {content}', inline=False)

        button = discord.ui.Button(style=discord.ButtonStyle.green, label='Jump to original message', url=message.jump_url)
        view = discord.ui.View(timeout=None)
        view.add_item(button)

        return (heading, embed, view)

    async def add_star(self, payload: discord.RawReactionActionEvent) -> None:
        if str(payload.emoji) != '\N{WHITE MEDIUM STAR}':
            return

        starboard = await self.get_starboard(payload.guild_id)
        starboard_channel = starboard.channel
        if starboard_channel is None:
            raise StarboardError('\N{NO ENTRY} Starboard not found.')

        overwrites = starboard_channel.overwrites_for(self.bot.user)
        if not (overwrites.send_messages and overwrites.read_messages and overwrites.manage_messages):
            raise StarboardError(
                f'\N{NO ENTRY SIGN} I do not have permissions to send/manage messages in {starboard_channel.mention}.'
            )

        try:
            message = await self.get_message(payload.channel_id, payload.message_id)
            if message is None:
                raise StarboardError('\N{WARNING SIGN} The message was deleted.')
        except discord.Forbidden:
            raise StarboardError('\N{NO ENTRY SIGN} Permission error: Could not find message.')

        stars = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == '\N{WHITE MEDIUM STAR}':
                stars = reaction.count
                break

        if starboard.locked:
            raise StarboardError('\N{NO ENTRY SIGN} Starboard is locked.')

        if not overwrites.send_messages and not overwrites.manage_messages:
            raise StarboardError(
                f'\N{NO ENTRY SIGN} I do not have permissions to send/manage messages in {starboard_channel.mention}.'
            )

        if stars < starboard.post_requirement:
            return

        async with self.pool.acquire(timeout=100) as conn:
            big_ahh_query = """
                WITH inserted AS (
                        INSERT INTO StarEntry (message_id, guild_id, author_id)
                        VALUES ($1, $2, $3)
                    
                        ON CONFLICT(message_id) DO UPDATE SET
                        total_stars = $4
                        RETURNING message_id, bot_message_id, created_on
                )
                SELECT Starer.user_id, bot_message_id, created_on
                FROM inserted LEFT JOIN Starer
                ON inserted.message_id = Starer.message_id
                """
            record: asyncpg.Record = await conn.fetchrow(
                big_ahh_query, payload.message_id, payload.guild_id, payload.message_author_id, stars
            )

            bot_message_id = record[1]
            created_on = record[2]
            content_message = await self.create_star_message(message, stars, created_on)
            heading = content_message[0]
            embed = content_message[1]
            view = content_message[2]

            # create the new entry
            try:
                query = """INSERT INTO Starer (user_id, message_id, guild_id) VALUES ($1, $2, $3)"""
                await conn.execute(query, payload.user_id, payload.message_id, payload.guild_id)
            except asyncpg.UniqueViolationError:
                raise StarboardError('\N{WHITE QUESTION MARK ORNAMENT} You already starred this message.')

            if bot_message_id is not None:
                try:
                    bot_entry_message = await self.get_message(starboard_channel.id, bot_message_id)
                    if bot_entry_message is None:
                        raise StarboardError('\N{WARNING SIGN} Could not find the bots original message.')

                    await bot_entry_message.edit(content=heading, embed=embed, view=view)
                    return
                except discord.Forbidden:
                    return

            bot_message = await starboard_channel.send(content=heading, embed=embed, view=view)
            content_id = bot_message.id
            query = """UPDATE StarEntry SET bot_message_id=$1 WHERE message_id=$2"""
            await conn.execute(query, content_id, message.id)

    async def remove_star(self, payload: discord.RawReactionActionEvent) -> None:
        if str(payload.emoji) != '\N{WHITE MEDIUM STAR}':
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        # add to cache first
        chan = await self.bot.fetch_channel(payload.channel_id)
        msg = await chan.fetch_message(payload.message_id)

        self.message_cache[payload.message_id] = msg
        await self.add_star(payload)

        await asyncio.sleep(5)
        await msg.add_reaction('\N{WHITE MEDIUM STAR}')

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        starboard = await self.get_starboard(payload.guild_id)
        if starboard.channel is None:
            return

        query = """SELECT message_id, bot_message_id FROM StarEntry WHERE guild_id=$1"""
        record = await self.pool.fetchrow(query, payload.guild_id)

        if record is None:
            return

        bot_message_id = record[1]

        async with self.pool.acquire(timeout=200) as conn:
            conn: asyncpg.Connection
            query = """DELETE FROM StarEntry WHERE message_id=$1"""
            await conn.execute(query, payload.message_id)
            try:
                if bot_message_id is None:
                    return
                try:
                    message = await self.get_message(starboard.channel_id, bot_message_id)
                    if message is None:
                        return
                    await message.delete()
                except discord.Forbidden:
                    raise StarboardError('\N{WARNING SIGN} Could not access message due to permission level.')
            except discord.DiscordServerError:
                return
            except Exception:
                return

    @commands.hybrid_group(fallback='create')
    @commands.has_permissions(manage_guild=True)
    async def starboard(self, ctx: GuildContext, category: discord.CategoryChannel, *, channel_name: str = 'starboard') -> None:
        """Creates a new Starboard if one doesnt exist.

        Args:
            category (discord.CategoryChannel): The category to place the Starboard channel under.
            channel_name (str, optional): The name of the Starboard channel. Defaults to 'starboard'.
        """
        await ctx.defer()
        guild_id = ctx.guild.id
        starboard = await self.get_starboard(guild_id)
        if hasattr(starboard, 'locked'):
            if starboard.channel is None:
                confirmation = await ctx.confirm(
                    'The Starboard channel was deleted. Would you like to start over?',
                    '\N{WHITE QUESTION MARK ORNAMENT} Could not find Starboard',
                )
                if confirmation is False:
                    await ctx.reply('\N{WHITE QUESTION MARK ORNAMENT} Starboard creation aborted.')
                    return
                elif confirmation is None:
                    await ctx.reply('You took too long. Aborted.')
                    return
                query = """DELETE FROM Starboards WHERE guild_id=$1"""
                await self.pool.execute(query, guild_id)
            else:
                await ctx.reply(f'It looks like you already have a Starboard for this server: {starboard.channel.mention}...')
                return
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
            starboard_channel = await ctx.guild.create_text_channel(
                channel_name,
                reason=f'\N{DIZZY SYMBOL} Starboard created by: {ctx.author.name}. (ID: #{ctx.author.id})',
                overwrites=overwrites,
                category=category,
            )

            try:
                query = """INSERT INTO Starboards (guild_id, channel_id) VALUES (
                        $1,
                        $2
                )"""
                await self.pool.execute(query, guild_id, starboard_channel.id)
                await ctx.reply(f'\N{DIZZY SYMBOL} Starboard creation successful: {starboard_channel.mention}')
            except Exception:
                await ctx.reply('An unkown error occured.')
                return
        except discord.Forbidden:
            await ctx.reply('\N{EXCLAMATION QUESTION MARK} I do not have enough permissions to create this channel.')
            return
        except StarboardError:
            return
        except Exception:
            await ctx.reply('An unknown error occured.')
            return

    @starboard.group()
    @starboard_only()
    async def threshold(self, ctx: StarContext) -> None:
        """Shows many \N{WHITE MEDIUM STAR}'s a message needs."""
        await ctx.defer()
        starboard = ctx.starboard
        await ctx.reply(f'Current requirement: {starboard.post_requirement}')

    @threshold.command()
    @starboard_only()
    async def update(self, ctx: StarContext, count: int) -> None:
        """Changes how many \N{WHITE MEDIUM STAR}'s a message needs.

        Args:
            count (int): The number of \N{WHITE MEDIUM STAR}'s a message needs.
        """
        await ctx.defer()
        starboard = ctx.starboard
        if count <= 0:
            raise StarboardError('❓ Threshold must be greater than 0.')

        query = """UPDATE Starboards SET post_requirement = $1 WHERE guild_id = $2"""
        await self.pool.execute(query, count, ctx.guild.id)
        starboard.post_requirement = count
        await ctx.reply(f'Star requirement set to: {count}')


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Starboard(bot))
