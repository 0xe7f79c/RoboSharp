from discord.ext import commands

from cogs.util.context import RContext

from cogs.bot import RSharp
from discord.app_commands import AppCommandError


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Help(bot=bot))


class HelpError(ValueError, AppCommandError):
    """A hybrid help module error.

    Args:
        ValueError (ValueError): Fulfills the class relationship to satisfy the text command errors.
        AppCommandError (_type_): Fulfills the class relationship to satisfy the slash command errors.
    """

    pass


UNKNOWN_EMOJI = "\N{BLACK QUESTION MARK ORNAMENT}"


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
                await ctx.send("{}{}".format(UNKNOWN_EMOJI, str(error)))

    @commands.hybrid_command(
        name="help",
        guild_only=678655372197625858,
    )
    async def help(self, ctx: RContext):
        raise HelpError("Unknown command/module. (Did you type it right?)")
