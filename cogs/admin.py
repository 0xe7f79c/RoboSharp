from discord.ext import commands

from core.bot import RSharp


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Admin(bot=bot))


class Admin(commands.Cog):
    def __init__(self, bot: RSharp):
        self.bot = bot
