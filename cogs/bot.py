from typing import Any, Optional, Union, Type, Unpack, override

import discord
from discord import Client, Intents, Interaction, User
from discord.ext import commands
from cogs.util.context import RContext

MAY_USER_ID = 882316761268113418


class RSharp(commands.Bot):
    def __init__(self, prefix: str) -> None:
        intents = Intents.all()
        super().__init__(command_prefix=prefix, intents=intents)

    async def get_context(
        self,
        origin: Union[discord.Message, discord.Interaction[Client]],
        /,
        *,
        cls: type[commands.Context[Any]] = RContext,
    ) -> RContext:
        return await super().get_context(origin, cls=RContext)

    async def send_pickable(self):
        pass
