from discord.app_commands import AppCommandError
from discord.ext import commands
from discord.ext.commands import CommandError

import core


async def setup(bot: core.RSharp) -> None:
    await bot.add_cog(Help(bot=bot))


class HelpError(ValueError, AppCommandError):
    """An adapter class that satisifies both hybrid and text exceptions."""


class Help(core.Cog, pictograph='\N{BLACK QUESTION MARK ORNAMENT}'):
    """
    Hello, welcome to the help menu! To navigate this bot, you can use either
    the command prefix, or its slash-command counterpart!
    """

    def __init__(self, bot: core.RSharp) -> None:
        self.bot = bot

    async def cog_command_error(
        self, ctx: core.GuildContext, error: CommandError
    ) -> None:
        if isinstance(error, Exception):
            error = error.original
            if isinstance(error, HelpError):
                await ctx.send(f'{self.pictograph}{error!s}')

    @commands.hybrid_group(name='help')
    async def _help(self, ctx: core.GuildContext, name: str) -> None:
        """Displays a menu of available commands"""
        await ctx.defer()

        cog: core.Cog = self.bot.get_cog(name)
        if cog is None:
            raise HelpError(f'Unknown module: {name}')

        await ctx.reply(cog.description)

    @_help.command(aliases=['source'])
    async def src(self, ctx: core.GuildContext) -> None:
        link = core.SRC_LINK
        await ctx.reply(link, ephemeral=True)
