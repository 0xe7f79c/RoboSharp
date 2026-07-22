import asyncio
from typing import Any, Dict

import asyncpg
import discord
from discord import Guild
from discord.ext import commands

CONFIRM_AGREE = ['yes', 'y', 'yep', 'mhm', 'sure', 'yea', 'yeah']


class RContext(commands.Context):
    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        super().__init__(**kwargs)

    async def prompt(self, message: str) -> None:
        await self.send(message)

        def check(msg: discord.Message) -> bool:
            return msg.author == self.author and msg.channel == self.channel

        try:
            confirm = await self.bot.wait_for('message', check=check, timeout=30.0)
            content = confirm.content.lower()
            if content in ['yes', 'y', 'true']:
                return True
            if content in ['no', 'false', 'n']:
                return False
        except asyncio.TimeoutError:
            await self.send('Took too long, aborting...')


class GuildContext(RContext):
    guild: Guild
    pool: asyncpg.Pool
