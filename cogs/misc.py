from typing import Any, List, Mapping, Optional

import discord
from discord.app_commands import CommandSyncFailure
from discord.ext import commands

from bot import RSharp
from cogs.utils.context import GuildContext

SOURCE_CODE = 'https://github.com/0xe7f79c/RoboSharp'
SCOPE_COPY_GUILD = 'copy-guild'
SCOPE_COPY_GLOBAL = 'copy-global'


class HelpEmbed(commands.HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]):
        embed = discord.Embed(
            color=discord.Color.og_blurple(),
            title='About',
            description='Hello, welcome to the help menu! Use the categories below to explore this bots features. You can also type `/` to see application commands.',
        )

        for cog in mapping.keys():
            if cog is not None:
                cog_name = cog.qualified_name

                if hasattr(cog, 'cog_emoji'):
                    emoji = cog.cog_emoji()
                    cog_name = f'{emoji} {cog_name}'

                embed.add_field(name=cog_name, value=f'{cog.description}', inline=False)

        embed.set_footer(
            text=f'Tip: Use {self.context.prefix}help `Module` to get commands that lie in a specific module.', icon_url=None
        )

        await self.context.reply(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        name = cog.qualified_name
        description = cog.description

        if hasattr(cog, 'cog_emoji'):
            emoji = cog.cog_emoji()
            name = f'{emoji} {name}'

        embed = discord.Embed(
            color=discord.Color.og_blurple(),
            title=name,
            description=description,
        )

        for command in cog.get_commands():
            if command.hidden:
                continue

            command_name = command.name
            command_docstr = command.short_doc

            embed.add_field(name=command_name, value=command_docstr)

        return await self.context.reply(embed=embed)

    async def send_command_help(self, command: commands.Command[Any, ..., Any]):
        cog: commands.Cog = command.cog
        name = cog.qualified_name
        cog_doc = cog.description
        if hasattr(cog, 'cog_emoji'):
            emoji = cog.cog_emoji()
            name = f'{emoji} {name}'

        embed = discord.Embed(color=discord.Color.og_blurple(), title=name, description=f'{cog_doc}')

        command_name = command.name
        command_breif = command.short_doc
        command_sig = command.signature

        has_arg = len(command_sig) > 0
        prefix = self.context.prefix

        if has_arg:
            command_usage = f'{prefix}{command_name} {command.signature}'
        else:
            command_usage = f'{prefix}{command_name}'

        embed.add_field(name=command_name, value=command_breif, inline=False)
        embed.add_field(name='Usage', value=command_usage, inline=False)

        await self.context.reply(embed=embed)

    async def send_group_help(self, group: commands.Group[Any, ..., Any]):
        embed = discord.Embed(
            color=discord.Color.og_blurple(),
            title=f'Command group: `{group.name}`',
            description='Below are the commands inside this group.',
        )

        for command in group.commands:
            if command.hidden:
                continue

            name = command.name
            description = command.short_doc

            if hasattr(command, 'cog_emoji'):
                emoji = command.cog_emoji()
                name = f'{emoji} {name}'

            embed.add_field(name=name, value=f'> {description}', inline=False)

        embed.set_footer(
            text=f'Tip: Use `{self.context.prefix}help <group> <command name>` to get more information of a command in this group.',
            icon_url=None,
        )

        return await self.context.reply(embed=embed)


class Misc(commands.Cog):
    """Miscellaneous commands/features."""

    def __init__(self, bot: RSharp) -> None:
        self.bot = bot
        self.bot.help_command = HelpEmbed()

    def cog_emoji(self) -> str:
        return '\N{WHITE QUESTION MARK ORNAMENT}'

    @commands.is_owner()
    @commands.command(hidden=True)
    async def sync(self, ctx: GuildContext, scope: str = SCOPE_COPY_GUILD) -> None:
        """Synchronizes the bots commands to this guild."""
        if ctx.guild is None:
            return await ctx.reply('\N{WHITE QUESTION MARK ORNAMENT} This command must be ran in a Guild.')

        if scope == SCOPE_COPY_GLOBAL:
            scope = None
        else:
            scope = ctx.guild

        self.bot.tree.copy_global_to(guild=scope)
        try:
            commands = await self.bot.tree.sync(guild=scope)
            return await ctx.reply(f'\N{OK HAND SIGN} Synchronized all app commands. ({len(commands)} total commands)')
        except discord.Forbidden:
            return await ctx.reply('\N{NO ENTRY} Could not sync. (No `applications.commands` scope in guild...)')
        except CommandSyncFailure:
            return await ctx.reply('\N{NO ENTRY} Could not sync. (There is an error in one of your commands...)')
        except Exception:
            return await ctx.reinvoke('\N{WHITE QUESTION MARK ORNAMENT} Something went wrong. (Internal error)')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def clear(self, ctx: GuildContext, scope: str = SCOPE_COPY_GUILD) -> None:
        """Clears the command tree for this guild."""

        if ctx.guild is None:
            return await ctx.reply('\N{WHITE QUESTION MARK ORNAMENT} This command must be ran in a Guild.')

        if scope == SCOPE_COPY_GLOBAL:
            scope = None
        else:
            scope = ctx.guild

        self.bot.tree.clear_commands(guild=scope)
        try:
            commands = await self.bot.tree.sync(guild=scope)
            return await ctx.reply(f'\N{OK HAND SIGN} Synchronized all app commands. ({len(commands)} total commands)')
        except discord.Forbidden:
            return await ctx.reply('\N{NO ENTRY} Could not sync. (No `applications.commands` scope in guild...)')
        except CommandSyncFailure:
            return await ctx.reply('\N{NO ENTRY} Could not sync. (There is an error in one of your commands...)')
        except Exception:
            return await ctx.reinvoke('\N{WHITE QUESTION MARK ORNAMENT} Something went wrong. (Internal error)')


async def setup(bot: RSharp) -> None:
    await bot.add_cog(Misc(bot=bot))
