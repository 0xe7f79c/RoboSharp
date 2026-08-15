from logging import Logger
from typing import Any, Type, Union

import asyncpg
import discord
from discord import Client, Intents, Message
from discord.ext import commands

from cogs.utils.config import Config
from cogs.utils.context import GuildContext, RContext
from cogs.utils.logging import LogHandler

DEBUG = True


class RSharp(commands.Bot):
    log_handler: LogHandler
    logger: Logger
    pool: asyncpg.Pool

    def __init__(self, prefix: str, config: Config) -> None:
        intents = Intents.all()
        super().__init__(command_prefix=prefix, intents=intents)
        RContext.config = config

    async def get_context(
        self,
        origin: Union[discord.Message, discord.Interaction[Client]],
        /,
        *,
        cls: Type[commands.Context[Any]] = RContext,
    ) -> RContext:
        return await super().get_context(origin, cls=RContext)

    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return None

        content: str = message.clean_content
        self.logger.info(content)
        return await super().on_message(message)

    async def on_command_error(
        self,
        context: Union[GuildContext, RContext],
        exception: Exception,
    ) -> None:
        content: str = str(exception)
        clazz: type = type(exception)
        self.logger.info(f'{clazz.__name__}: {content}')
