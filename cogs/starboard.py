from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import asyncpg
import discord
from discord.app_commands import AppCommandError
from discord.ext import commands, tasks
from discord.ext.commands._types import Check

from cogs.utils.context import GuildContext

if TYPE_CHECKING:
    from ..bot import RSharp


class ValidStarChannel(discord.TextChannel):
    pass


MAX_FIELD_LEN = 120
ALLOWED_MIMES = ['image/jpeg', 'image/webp', 'image/png', 'image/gif']
VALID_IMAGE_ATTACHMENTS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
UNKNOWN_ICON_URL = 'https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcGt0eHB6azZzdGVnb2l6Y3NwcW14MHI4bWNua2tpc2ZhNG9ranRiaiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/YhxdbIJZHVHMDmyHJp/giphy.gif'


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
            await ctx.reply('\N{NO ENTRY SIGN} Could not find/access this guilds Starboard.')
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

        # message id -> message
        self.message_cache: Dict[int, discord.Message] = {}
        self.clear_message_cache_loop.start()

    def cog_emoji(self) -> str:
        return '\N{DIZZY SYMBOL}'

    async def cog_command_error(self, ctx, error) -> None:
        if isinstance(error, commands.HybridCommandError):
            error = error.original
        if isinstance(error, StarboardError):
            await ctx.send(str(error))

    @tasks.loop(minutes=25, count=None)
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
        try:
            if message_id in self.message_cache:
                msg = self.message_cache[message_id]
                return msg

            channel = await self.bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            self.message_cache.update({message_id: message})
            return message
        except discord.NotFound:
            return None

    def handle_message_length(self, clean_content: str, jump_url: str) -> str:
        if len(clean_content) > MAX_FIELD_LEN:
            content = f'{clean_content[0:MAX_FIELD_LEN]}'
            content += f'[...]({jump_url})'
            return content
        else:
            return clean_content

    def handle_attachment(self, message: discord.Message, embed: discord.Embed):
        attachments: List[discord.Attachment] = message.attachments

        if len(attachments) > 0:
            first = attachments[0]
            file_extension = first.filename

            if first.content_type in ALLOWED_MIMES or file_extension.endswith(VALID_IMAGE_ATTACHMENTS):
                embed.add_field(name='Image', value=f'[Download]({first.url})', inline=False)
                embed.set_image(url=first.url)
            else:
                embed.add_field(name='File', value=f'[View content]({message.jump_url})', inline=False)

    def parse_metadata(self, message: discord.Message, embed: discord.Embed):
        self.handle_attachment(message, embed)

        clean_msg = message.clean_content
        if not len(clean_msg) <= 0:
            embed.add_field(name='Message', value=clean_msg, inline=False)

        snapshots = message.message_snapshots
        if not snapshots == []:
            first = snapshots[0]
            fwd_content = self.handle_message_length(first.content, message.jump_url)
            cached_msg = first.cached_message

            if cached_msg is not None:
                who = cached_msg.author
                where = cached_msg.guild
                embed.add_field(name='From...', value=f'[{where.name}]({cached_msg.jump_url})', inline=False)
                embed.add_field(name='Original author', value=f'{who.name}', inline=False)
                embed.add_field(name='Message', value=f'{fwd_content}', inline=False)
                self.handle_attachment(cached_msg, embed)
            else:
                if len(fwd_content) > 0:
                    embed.add_field(name='(Forwarded) Message', value=f'{fwd_content}', inline=False)

        ref = message.reference
        if ref is not None:
            resolved = ref.resolved
            if resolved is not None:
                if resolved is discord.DeletedReferencedMessage:
                    return
                src_msg = resolved.clean_content  # type: ignore
                src_msg = self.handle_message_length(src_msg, resolved.jump_url)  # type: ignore
                who = resolved.author
                name = who.name
                if name == message.author.name:
                    name = 'Themselves'
                embed.add_field(name='Replying to...', value=f'{name}', inline=False)
                if resolved.embeds == []:
                    if not len(src_msg) == 0:
                        embed.add_field(name='Source', value=f'> {src_msg}', inline=False)
                    self.handle_attachment(resolved, embed)

    async def create_star_message(self, message: discord.Message, stars: int) -> Tuple[str, discord.Embed, discord.ui.View]:
        embed_col = self.get_color_brightness(stars)
        embed = discord.Embed(color=embed_col)

        display_emoji = self.get_emoji(stars)
        heading = f'{display_emoji} {stars} | {message.channel.mention}'

        author_name = message.author.name
        author_icon: Optional[discord.Asset] = message.author.avatar
        if author_icon is None:
            embed.set_author(name=author_name, icon_url=UNKNOWN_ICON_URL)
        else:
            embed.set_author(name=author_name, icon_url=author_icon.url)

        self.parse_metadata(message, embed)

        button = discord.ui.Button(
            style=discord.ButtonStyle.green,
            label='Jump to message',
            url=message.jump_url,
        )

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

        async with self.pool.acquire(timeout=50) as conn:
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
                big_ahh_query,
                payload.message_id,
                payload.guild_id,
                payload.message_author_id,
                stars,
            )

            bot_message_id = record[1]
            # created_on = record[2]
            content_message = await self.create_star_message(message, stars)
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        chan = await self.bot.fetch_channel(payload.channel_id)
        msg = await chan.fetch_message(payload.message_id)
        self.message_cache.update({payload.message_id: msg})
        await self.add_star(payload)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        starboard = await self.get_starboard(payload.guild_id)
        if starboard.channel is None:
            return

        query = """SELECT bot_message_id FROM StarEntry WHERE message_id=$1"""
        record = await self.pool.fetchrow(query, payload.message_id)

        if record is None:
            return

        bot_message_id = record[0]

        async with self.pool.acquire(timeout=50) as conn:
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
    async def starboard(
        self,
        ctx: GuildContext,
        category: discord.CategoryChannel,
        *,
        channel_name: str = 'starboard',
    ) -> None:
        """Creates a new starboard under a specific category."""
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
                    view_channel=True,
                    manage_messages=True,
                    send_messages=True,
                    read_messages=True,
                    pin_messages=True,
                ),
                default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    manage_messages=False,
                    send_messages=False,
                    pin_messages=False,
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
            await ctx.reply('\N{WHITE QUESTION MARK ORNAMENT} I do not have enough permissions to create this channel.')
            return

        except StarboardError:
            return

        except Exception:
            await ctx.reply('An unknown error occured.')
            return

    @starboard.group(name='threshold', invoke_without_command=True)
    @starboard_only()
    async def _threshold(self, ctx: StarContext) -> None:
        """Shows many \N{WHITE MEDIUM STAR}'s a message needs."""
        await ctx.defer()
        starboard = ctx.starboard
        await ctx.reply(f"A message needs: {starboard.post_requirement} \N{WHITE MEDIUM STAR}'s to become a Starboard post.")

    @_threshold.command()
    @commands.bot_has_guild_permissions(manage_guild=True)
    @starboard_only()
    async def set(self, ctx: StarContext, amount: int):
        """Sets the starboard threshold to a new value."""
        if amount > 50:
            return await ctx.reply('\N{WHITE QUESTION MARK ORNAMENT} The requirement must be a reasonable amount.')

        starboard = ctx.starboard
        if starboard.post_requirement == amount:
            return await ctx.reply(
                f"\N{WHITE QUESTION MARK ORNAMENT} The provided threshold is already set to {amount} \N{WHITE MEDIUM STAR}'s"
            )

        query = """UPDATE Starboards SET post_requirement=$1 WHERE guild_id=$2"""
        await self.pool.execute(query, amount, ctx.guild.id)
        starboard.post_requirement = 3
        return await ctx.reply(f"\N{OK HAND SIGN} Requirement changed to: {amount} \N{WHITE MEDIUM STAR}'s")

    @starboard.command()
    @starboard_only()
    async def lock(self, ctx: StarContext) -> None:
        """
        Locks the Starboard.
        """
        await ctx.defer()

        starboard = ctx.starboard

        if starboard.locked:
            raise StarboardError('\N{WHITE QUESTION MARK ORNAMENT} Starboard is already locked.')

        query = """UPDATE Starboards SET locked=$1 WHERE guild_id=$2"""
        await self.pool.execute(query, True, ctx.guild.id)
        starboard.locked = True
        await ctx.reply('Starboard locked.')

    @starboard.command()
    @starboard_only()
    async def unlock(self, ctx: StarContext) -> None:
        """
        Unlocks the Starboard.
        """
        await ctx.defer()

        starboard = ctx.starboard

        if not starboard.locked:
            raise StarboardError('\N{WHITE QUESTION MARK ORNAMENT} The starboard is already unlocked.')

        query = """UPDATE Starboards SET locked=$1 WHERE guild_id=$2"""
        await self.pool.execute(query, False, ctx.guild.id)
        starboard.locked = False
        await ctx.reply('Starboard unlocked.')


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Starboard(bot))
