from discord.app_commands import AppCommandError
from discord.ext import commands
from discord.ext.commands import CommandError

import core


async def setup(bot: core.RSharp) -> None:
    await bot.add_cog(Help(bot=bot))


class HelpError(ValueError, AppCommandError):
    """An adapter class that satisifies both hybrid and text exceptions."""

    pass


class Help(core.Cog, pictograph='\N{BLACK QUESTION MARK ORNAMENT}'):
    """
    Hello, welcome to the help menu! To navigate this bot, you can use either
    the command prefix, or its slash-command counterpart!
    """  # noqa: E501

    def __init__(self, bot: core.RSharp) -> None:
        self.bot = bot

    async def cog_command_error(
        self, ctx: core.GuildContext, error: CommandError
    ) -> None:
        if isinstance(error, Exception):
            error = error.original
            if isinstance(error, HelpError):
                await ctx.send('{}{}'.format(self.pictograph, str(error)))

    @commands.hybrid_command(
        name='help',
        guild_only=678655372197625858,
    )
    async def help(self, ctx: core.GuildContext, *, name: str = 'Help') -> None:
        """Displays a menu of available commands"""
        cog: core.Cog = self.bot.get_cog(name)
        if cog is None:
            raise HelpError('Unknown module: {}'.format(name))

        await ctx.send(cog.description)
