import core


async def setup(bot: core.RSharp) -> None:
    await bot.add_cog(Admin(bot=bot))


class Admin(core.Cog):
    """Manages the admin settings for this discord server
    by default, the bot assumes **zero permissions** beyond reading/writing
    to unrestricted channels. For admin commands to work, you must provide the:
    `Manage Roles` permission."""

    def __init__(self, bot: core.RSharp) -> None:
        self.bot = bot
