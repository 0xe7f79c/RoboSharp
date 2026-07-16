from discord.app_commands import AppCommandError
from discord.ext import commands

from core.bot import RSharp
from core.context import GuildContext


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Help(bot=bot))


class HelpError(ValueError, AppCommandError):
    """An adapter class that satisifies both hybrid and text exceptions."""

    pass


UNKNOWN_EMOJI = '\N{BLACK QUESTION MARK ORNAMENT}'


class Help(commands.Cog):
    """
    A module that helps you navigate this bots features.
    """

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, Exception):
            error = error.original
            if isinstance(error, HelpError):
                await ctx.send('{}{}'.format(UNKNOWN_EMOJI, str(error)))

    @commands.hybrid_command(
        name='help',
        guild_only=678655372197625858,
    )
    async def help(self, ctx: GuildContext, *, name: str = 'help'):
        await ctx.send('[dbg] todo')
