from typing import KeysView, Mapping

from discord import Color, Embed
from discord.ext import commands

from cogs.util.context import RContext

from cogs.bot import RSharp
from cogs.util.pages import Paginator


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Help(bot=bot))


class HelpError(ValueError):
    pass


class Help(commands.Cog):
    """
    A module that helps you navigate this bots features.
    """

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot

    def default_menu(self, cogs: Mapping[str, commands.Cog]) -> Embed:
        msg = ""
        embed = Embed(color=Color.greyple(), title="Showing list of categories")
        cog_names: KeysView[str] = cogs.keys()

        for name in cog_names:
            module = cogs[name]
            module_name: str = module.qualified_name

            app_command_count: int = len(module.get_app_commands())
            text_command_count: int = len(module.get_commands())
            command_sum = app_command_count + text_command_count

            plural_label = "command" if command_sum == 1 else "commands"

            module_desc = module.description

            msg = "└─`{} {}...`".format(command_sum, plural_label)
            embed.add_field(name="*{}*".format(module_name), value=msg, inline=True)

        return embed

    @commands.command()
    async def help(self, ctx: RContext):
        cogs = self.bot.cogs
        menu = self.default_menu(cogs=cogs)
        view = Paginator(document="iwuoiaeghsiuerghiruseherheisurrg")
        await ctx.send(embed=menu, view=view)
