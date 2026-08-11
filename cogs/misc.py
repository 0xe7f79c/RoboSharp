import discord
from discord.app_commands import CommandSyncFailure
from discord.ext import commands

from bot import RSharp
from cogs.utils.context import GuildContext

SOURCE_CODE = 'https://github.com/0xe7f79c/RoboSharp'


class Misc(commands.Cog):
    """Miscellaneous commands/features."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def sync(self, ctx: GuildContext) -> None:
        """Synchronizes the bots commands to this guild."""
        self.bot.tree.copy_global_to(ctx.guild)
        try:
            commands = await self.bot.tree.sync(ctx.guild)
            return await ctx.reply(f'\N{OK HAND SIGN} Synchronized all app commands. ({len(commands)} total commands)')
        except discord.Forbidden:
            return await ctx.reply('\N{NO ENTRY} Could not sync. (No `applications.commands` scope in guild...)')
        except CommandSyncFailure:
            return await ctx.reply('\N{NO ENTRY} Could not sync. (There is an error in one of your commands...)')
        except Exception:
            return await ctx.reinvoke('\N{WHITE QUESTION MARK ORNAMENT} Something went wrong. (Internal error)')


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Misc(bot=bot))
