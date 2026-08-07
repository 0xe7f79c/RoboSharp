import asyncio
import random
from typing import Optional

import discord
from discord.app_commands import AppCommandError
from discord.ext import commands

from bot import DEBUG, GuildContext, RSharp
from cogs.admin import AdminError
from cogs.starboard import Check

PSINI_USER_ID = 593294576026910720

if not DEBUG:
    LANCE_USER_ID = 514542702013186049
else:
    LANCE_USER_ID = PSINI_USER_ID

POLL_EMOJIS = ['\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}']


class LanceError(ValueError, AppCommandError):
    pass


def lance_only() -> Check[GuildContext]:
    async def wrapper(ctx: GuildContext) -> bool:
        if ctx.guild is None:
            return False
        elif ctx.author.id != LANCE_USER_ID:
            raise LanceError('This command can only be run by lance.')

        permissions = ctx.channel.permissions_for(ctx.author)
        if not permissions.administrator:
            raise LanceError('\N{NO ENTRY} LanceUtils is blocked if Lance isnt Admin.')

        return True

    return commands.check(wrapper)


class LanceUtils(commands.Cog):
    """Various lance only commands (if he is moderator...)"""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, Exception):
            error = error.original
            if isinstance(error, LanceError):
                return await ctx.send(str(error))

    @commands.hybrid_group(name='lance')
    @lance_only()
    async def lance_group(self, ctx: GuildContext) -> None:
        """More LanceUtils commands."""

    @lance_group.command()
    @lance_only()
    async def votekick(self, ctx: GuildContext, member: Optional[discord.Member], *, delay: int = 3 * 60) -> None:
        """Creates a votekick.

        Args:
            member (Optional[discord.Member]): The member to boot. If one isnt provided, will resort to kicking a random user.
            delay (Optional[discord.Member]): The amount of time (in seconds) to wait before poll results are collected.
        """
        if member is None:
            confirm = await ctx.confirm(title='Member not provided', msg='Would you like to pick a random user to kick?')
            if confirm is None:
                return await ctx.reply('\N{WHITE QUESTION MARK ORNAMENT} You took too long. Aborted kick.')
            elif not confirm:
                raise LanceError('\N{NO ENTRY} No user provided.')

            member_seq = ctx.guild.members

            victim = random.choice(member_seq)
            while True:
                victim = random.choice(member_seq)
                if victim.id != PSINI_USER_ID and not victim.bot:
                    break
                else:
                    return await ctx.reply('\N{NO ENTRY} No members available to kick.')

            confirm = await ctx.confirm(title='Random user', msg=f'Attempting to kick random user: `{victim.name}`. Proceed?')
            if confirm is None:
                raise AdminError('You took too long. Aborted.')

            if not confirm:
                raise LanceError('\N{NO ENTRY} No user provided.')

            member = victim

        if member.id == PSINI_USER_ID:
            raise LanceError('\N{NO ENTRY} Nice try')

        embed = discord.Embed(
            color=discord.Color.og_blurple(),
            title='Vote kick',
            description=f'An active vote is set on {member.name}. You have {delay} seconds to make your decision.',
        )

        embed.set_footer(text='React with \N{WHITE HEAVY CHECK MARK} to vote for the kick, or \N{CROSS MARK} otherwise.')

        message = await ctx.send(content=f'(LanceUtils) Votekick initated (ID: {LANCE_USER_ID})', embed=embed)
        for emoji in POLL_EMOJIS:
            await message.add_reaction(emoji)

        await asyncio.sleep(delay)

        # re fetch the message
        message = await ctx.fetch_message(message.id)
        if message is None:
            return

        total_yes = 0
        total_no = 0

        reacts = message.reactions
        if reacts == []:
            return await message.reply('\N{WHITE QUESTION MARK ORNAMENT} Vote emojis cleared. No one will be kicked.')

        for reaction in reacts:
            emoji = reaction.emoji
            if str(emoji) in POLL_EMOJIS:
                if str(emoji) == POLL_EMOJIS[1]:
                    total_no = reaction.count - 1
                    continue

                total_yes = reaction.count - 1

        if total_yes == total_no:
            return await message.reply('\N{WHITE QUESTION MARK ORNAMENT} Vote was inconclusive. No one will be kicked.')
        elif total_yes > total_no:
            try:
                await member.kick(reason=f'(Majority vote) Kicked by Lance ID: #{LANCE_USER_ID}')
                return await message.reply(f'{member.name} has been kicked. (Majority vote)')
            except Exception:
                return await message.reply(f'Could not kick user: {member.name} (No kick permissions.)')

        return await message.reply(f'{member.mention} has been spared. (Majority vote)')


async def setup(bot: RSharp):
    await bot.add_cog(LanceUtils(bot=bot))
