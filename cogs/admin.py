from ast import Tuple
from itertools import batched
from typing import TYPE_CHECKING, List, Optional

import asyncpg
import discord
from discord.app_commands import AppCommandError
from discord.ext import commands

from bot import GuildContext

if TYPE_CHECKING:
    from ..bot import RSharp


class AdminError(ValueError, AppCommandError):
    pass


EMOJI_PER_PAGE = 4


class BannedEmojiConfig:
    def __init__(self, bot: RSharp, guild_id: int, emoji_id: int, record: asyncpg.Record) -> None:
        self.guild_id = guild_id
        self.emoji_id = emoji_id

        self.bot = bot

        if record is not None:
            self.reason = record[0]
        else:
            self.channel = None

    @property
    def emoji(self) -> Optional[discord.Emoji]:
        emoj = self.bot.get_emoji(self.emoji_id)
        return emoj


class BanEmojiPages(discord.ui.View):
    def __init__(self, author_id: int, record_list: List[BannedEmojiConfig], *, timeout=180):
        super().__init__(timeout=timeout)
        self.embed = discord.Embed(title='Currently banned emojis', color=discord.Color.og_blurple())
        self.author_id = author_id

        # ghetto pagination but idgaf
        self.pages = list(batched(record_list, n=EMOJI_PER_PAGE)) if record_list else [()]
        self.num_pages = len(self.pages)
        self.current_page = 0

        self.form_page()

    def form_page(self) -> None:
        self.embed.clear_fields()
        self.embed.title = f'Page: {self.current_page + 1}/{self.num_pages}'

        if not self.pages or not self.pages[self.current_page]:
            self.embed.description = 'No emojis.'
            return

        for content in self.pages[self.current_page]:
            emoji_id = content.emoji_id
            reason = content.reason
            if reason is None:
                reason = 'No reason given.'
            self.embed.add_field(name=f'ID: `{emoji_id}`', value=f'Reason: `{reason}`', inline=False)

    @discord.ui.button(label='<<')
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.form_page()
            await interaction.response.edit_message(embed=self.embed)
        else:
            await interaction.response.defer()

    @discord.ui.button(label='>>')
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.current_page < self.num_pages - 1:
            self.current_page += 1
            self.form_page()
            await interaction.response.edit_message(embed=self.embed)
        else:
            await interaction.response.defer()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.followup.send('I did not ask you.', ephemeral=True)
            return False
        return True


class Admin(commands.Cog):
    """Moderation tools for your discord server."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot
        self.pool = self.bot.pool

    async def cog_command_error(self, ctx, error):
        if isinstance(error, Exception):
            error = error.original
            if isinstance(error, AdminError):
                return await ctx.send(str(error))
            elif isinstance(error, asyncpg.DataError):
                return await ctx.send('The provided value is too big.')

    async def get_default_role(self, guild_id: int) -> Optional[discord.Role]:
        """Returns the Guilds default role."""
        async with self.pool.acquire() as conn:
            query = """SELECT role_id FROM GuildDefaultRole WHERE guild_id = $1"""
            record: asyncpg.Record = await conn.fetchrow(query, guild_id)

            if record is None:
                return None

            role_id: int = record[0]
            guild = self.bot.get_guild(guild_id)
            role = guild.get_role(role_id)

            if role is None:
                return None

            return role

    async def get_banned_emoji_info(self, emoji_id: int, guild_id: int) -> Optional[BannedEmojiConfig]:
        async with self.pool.acquire() as conn:
            query = """SELECT
                        reason AS "reason"
                        FROM BannedEmoji
                        WHERE guild_id=$1
                        AND emoji_id=$2"""
            record: asyncpg.Record = await conn.fetchrow(query, guild_id, emoji_id)
            conf = BannedEmojiConfig(self.bot, guild_id, emoji_id, record)
            return conf

    @commands.hybrid_group()
    @commands.has_guild_permissions(manage_roles=True)
    async def roles(self, ctx: GuildContext) -> None:
        """Several commands related to role creation/management.

        Args:
            ctx (GuildContext): _description_
        """

        default_role = await self.get_default_role(ctx.guild.id)
        if default_role is None:
            await ctx.reply('No default role found.')
            return

        role_id = default_role.id
        await ctx.reply(
            f'The default role for this guild is: {role_id}. Newly joined members will automatically be assigned this role.'
        )

    @roles.command(name='set')
    async def default(self, ctx: GuildContext, role: discord.Role) -> None:
        """Sets the default role for this guild.

        Args:
            ctx (GuildContext): _description_
            role (discord.Role): The role to set as the default role.
        """

        guild_id = ctx.guild.id
        role_id = role.id

        old_role = await self.get_default_role(guild_id)
        if old_role is not None:
            confirm = await ctx.confirm(
                title='Default role found',
                msg=f'Apparently, a default role exists but it was deleted: `{role.name}`. Is this true?',
            )

            if confirm is None:
                raise AdminError('You took too long. Default role has not been affected.')
            elif not confirm:
                await ctx.reply('\N{OK HAND SIGN} Kept old role.')
                return

            # delete old role then
            query = """DELETE FROM GuildDefaultRole WHERE guild_id=$1"""
            await self.pool.execute(query, guild_id)

        if ctx.me.top_role <= role:
            raise AdminError('Could not set role: The role is greater or equal than my own role in the hierarchy.')

        async with self.pool.acquire() as conn:
            try:
                query = """INSERT INTO GuildDefaultRole (guild_id, role_id) VALUES (
                    $1,
                    $2
                )"""
                await conn.execute(query, guild_id, role_id)
                await ctx.reply(f'Default role is set to: `{role.name}`')
                ctx.default_role = role
            except Exception:
                raise AdminError('An unknown (internal) error occured.')

    @commands.hybrid_group()
    @commands.has_guild_permissions(manage_emojis=True)
    async def emoji(self, ctx: GuildContext):
        """Commands to manage emojis.

        Args:
            ctx (GuildContext): _description_
        """

    @emoji.command()
    async def ban(self, ctx: GuildContext, emoji_id, reason: str) -> None:
        """Bans an emoji.

        Args:
            ctx (GuildContext): _description_
            emoji (int): The Emoji ID to ban from the server.
            reason (str): The message that pops up when a user reacts/sends an emoji.
        """
        config = await self.get_banned_emoji_info(int(emoji_id), ctx.guild.id)
        if hasattr(config, 'reason'):
            await ctx.reply(f'Apparently, the emoji ID: `{emoji_id}` is already banned.')
            return

        async with self.pool.acquire() as conn:
            query = """INSERT INTO BannedEmoji (emoji_id, guild_id, reason) VALUES (
                        $1, $2, $3    
                    )
            """
            try:
                await conn.execute(query, int(emoji_id), ctx.guild.id, reason)
                await ctx.reply(f'Banned emoji ID: {emoji_id}')
            except Exception as ex:
                print(str(ex))
                await ctx.reply('An internal error occured.')
                return

    @emoji.command()
    async def bans(self, ctx: GuildContext) -> None:
        """Lists the currently banned emojis.

        Args:
            ctx (GuildContext): _description_
        """

        query = """SELECT reason, emoji_id FROM BannedEmoji WHERE guild_id=$1"""
        record = await self.pool.fetch(query, ctx.guild.id)

        if record is None or record == []:
            return await ctx.reply('\N{WHITE QUESTION MARK ORNAMENT} You have not banned any emojis for this server.')

        converted_record = []
        for data in record:
            emoji_id = data['emoji_id']
            config = BannedEmojiConfig(self.bot, ctx.guild.id, emoji_id, data)
            converted_record.append(config)

        view = BanEmojiPages(ctx.author.id, converted_record)
        await ctx.send(view=view, embed=view.embed)

    @emoji.command()
    async def unban(self, ctx: GuildContext, emoji_id: str) -> None:
        """Lifts the ban placed on an emoji.

        Args:
            ctx (GuildContext): _description_
            emoji_id (str): The Emoji ID to ban.
        """
        guild_id = ctx.guild.id

        # sigh
        try:
            emoji_id = int(emoji_id)
        except ValueError:
            raise AdminError('Emoji ID must be a number.')

        emoji = await self.get_banned_emoji_info(emoji_id, guild_id)
        if not hasattr(emoji, 'reason'):
            return await ctx.send('\N{WHITE QUESTION MARK ORNAMENT} That emoji ID is not banned.')

        async with self.pool.acquire(timeout=200) as conn:
            msg = f'Emoji ID: `{emoji_id}`'
            msg += f'Reason: `{emoji.reason}`'

            try:
                query = """DELETE FROM BannedEmoji WHERE guild_id=$1 AND emoji_id=$2"""
                await conn.execute(query, guild_id, emoji_id)
                return await ctx.reply(f'Unbanned Emoji ID: {emoji_id}.')
            except Exception:
                return await ctx.reply('An internal error occured.')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild_id = member.guild.id

        default_role = await self.get_default_role(guild_id)
        if default_role is None:
            return

        try:
            await member.add_roles(default_role, reason='(Guild configured) Default role added.')
        except Exception:
            # should probably handle this better but for resistivity purposes just handle it
            return

    async def grab_emojis(self, guild_id: int) -> Optional[List[Tuple[int]]]:
        query = """SELECT reason, emoji_id FROM BannedEmoji WHERE guild_id=$1"""
        record = await self.pool.fetch(query, guild_id)

        if record is None or record == []:
            return None

        emojis = []
        for data in record:
            emoji_id = data[1]
            reason = data[0]

            info = (emoji_id, reason)
            emojis.append(info)

        if emojis == []:
            return None

        return emojis

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        content = msg.content

        emojis = await self.grab_emojis(msg.guild.id)
        if emojis is None:
            return

        # if the bot sent it then it mightve been the ban reply above
        if msg.author.bot:
            return

        for emoji_data in emojis:
            emoji_id = emoji_data[0]
            reason = emoji_data[1]
            if str(emoji_id) in content:
                try:
                    await msg.channel.send(f'{msg.author.mention} That emoji is banned. Reason: {reason}', delete_after=3)
                    await msg.delete()
                    return
                except discord.Forbidden:
                    # do nothing
                    return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        channel = await self.bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        if payload.user_id == self.bot.user.id:
            return

        reactions = msg.reactions
        if not reactions:
            # this could happen weirdly enough
            return

        banned_emojis = await self.grab_emojis(payload.guild_id)

        for emoji_data in banned_emojis:
            emoji_id = emoji_data[0]
            reason = emoji_data[1]

            for reaction in reactions:
                reacted = reaction.emoji
                if reacted.id == emoji_id:
                    try:
                        user = self.bot.get_user(payload.user_id)

                        if user is None:
                            return

                        await channel.send(f'{user.mention} You cannot use that emoji. Reason: {reason}', delete_after=3)
                        await reaction.remove(user)
                        return
                    except discord.Forbidden:
                        return


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Admin(bot=bot))
