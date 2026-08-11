from discord.ext import commands

from bot import RSharp

SOURCE_CODE = 'https://github.com/0xe7f79c/RoboSharp'


class Misc(commands.Cog):
    """Miscellaneous commands/features."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Misc(bot=bot))
