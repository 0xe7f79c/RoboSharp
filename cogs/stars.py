from discord.ext import commands

import core


async def setup(bot: core.RSharp) -> None:
    await bot.add_cog(Stars(bot=bot))


class Stars(commands.Cog):
    """A feature to upvote posts."""

    def __init__(self, bot: core.RSharp) -> None:
        self.bot = bot
