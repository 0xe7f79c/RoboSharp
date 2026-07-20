from logging import Logger
from pathlib import Path
from typing import Any, Union

import asyncpg
import discord
from discord import Client, Intents, Message
from discord.ext import commands

from core import context
from core.logging import LogHandler

MAY_USER_ID = 882316761268113418


class RSharp(commands.Bot):
    log_handler: LogHandler
    logger: Logger
    pool: asyncpg.Pool

    def __init__(self, prefix: str) -> None:
        intents = Intents.all()
        super().__init__(command_prefix=prefix, intents=intents)

    async def get_context(
        self,
        origin: Union[discord.Message, discord.Interaction[Client]],
        /,
        *,
        cls: type[commands.Context[Any]] = context.RContext,
    ) -> context.RContext:
        return await super().get_context(origin, cls=context.RContext)

    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return None

        content: str = message.clean_content
        self.logger.info(content)
        return await super().on_message(message)

    async def on_command_error(
        self,
        context: Union[context.GuildContext, context.RContext],
        exception: Exception,
    ) -> None:
        content: str = str(exception)
        clazz: type = type(exception)
        self.logger.info(f'{clazz.__name__}: {content}')

    async def load_extensions(self, path: Path) -> None:
        if not path.is_dir:
            self.logger.warn(
                f'{path.name} is not a directory, Cogs will not be loaded.'
            )
            return

        for file in path.iterdir():
            cog_name: str = file.name
            if cog_name == '__pycache__':
                continue

            # remove .py
            cog_name: str = cog_name.removesuffix('.py')

            self.logger.info(f'Registering: {cog_name}')
            cog_path: str = f'cogs.{cog_name}'
            try:
                await self.load_extension(cog_path)
                self.logger.info(f'Loaded: {cog_name}')
            except Exception as ex:
                ex_str: str = str(ex)
                self.logger.error(f'Ignoring cog: {cog_name} due to error: {ex_str}')
