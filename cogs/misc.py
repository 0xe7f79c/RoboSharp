import discord
from discord.ext import commands

from bot import GuildContext, RSharp

SOURCE_CODE = 'https://github.com/0xe7f79c/RoboSharp'


class Misc(commands.Cog):
    """Miscellaneous commands/features."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot

    @commands.hybrid_group()
    async def misc(self, ctx: GuildContext) -> None:
        """Additional miscellaneous commands."""
        await ctx.send_help(ctx.command)

    @commands.hybrid_command()
    async def src(self, ctx: GuildContext) -> None:
        """Returns a link to the bots Github."""
        await ctx.send(f'My source code can be found here: {SOURCE_CODE}')

    @misc.command()
    async def who(self, ctx: GuildContext, member: discord.Member) -> None:
        """Provides a breif description on a member.

        Args:
            member (discord.Member): The member you would like a description of.
        """
        if member is None:
            return await ctx.reply('\N{WHITE QUESTION MARK ORNAMENT} Member not found.')

        await ctx.defer()

        embed = discord.Embed(color=discord.Color.orange(), title='User info')
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name='Username (Guild)', value=f'`{member.display_name}`')
        embed.add_field(name='Username (Global)', value=f'`{member.global_name}`')
        embed.add_field(name='Joined at', value=f'{member.joined_at}', inline=False)
        embed.add_field(name='Account created on', value=f'{member.created_at}', inline=False)
        perms = member.guild_permissions
        is_admin = perms.administrator
        embed.add_field(name='Admin', value=f'{is_admin}', inline=False)
        await ctx.reply(embed=embed)


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Misc(bot=bot))
