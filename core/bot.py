from logging import Logger
from typing import Any, Union

import discord
from discord import Client, Intents, Message
from discord.ext import commands

from core import context
from core.logging import LogHandler

MAY_USER_ID = 882316761268113418


class RSharp(commands.Bot):
    log_handler: LogHandler
    logger: Logger

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
