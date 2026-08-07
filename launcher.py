import asyncio

import asyncpg

from bot import RSharp
from cogs.utils.config import Config
from cogs.utils.logging import LogHandler

VANITY = r"""
  _____       _____ _                      
 |  __ \     / ____| |                     
 | |__) |   | (___ | |__   __ _ _ __ _ __  
 |  _  /     \___ \| '_ \ / _` | '__| '_ \ 
 | | \ \ _   ____) | | | | (_| | |  | |_) |
 |_|  \_(_) |_____/|_| |_|\__,_|_|  | .__/ 
                                    | |    
                                    |_|    
"""

extensions = ['cogs.starboard', 'cogs.admin', 'cogs.lance']


class Launcher:
    def __init__(self) -> None:
        config = Config()
        self.token = config.token
        self.prefix = config.prefix
        self.pg_dsn = config.pg_dsn
        self.remove_old_help = config.remove_default_help

        self.bot = RSharp(self.prefix)

    async def setup_pool(self, bot: RSharp) -> None:
        bot.pool = await asyncpg.create_pool(self.pg_dsn)

    async def run(self) -> None:
        async with self.bot as bot, LogHandler(log_type='discord') as logger:
            bot.log_handler = logger
            bot.logger = bot.log_handler.logger

            lines: list[str] = VANITY.splitlines()
            for line in lines:
                bot.logger.info(line)

            if self.remove_old_help:
                bot.logger.info('Uninstalling default help...')
                bot.remove_command('help')
                bot.logger.warning(f'Default {self.prefix}help command removed. You may need to register your own.')

            await self.setup_pool(bot)

            for cog in extensions:
                await self.bot.load_extension(cog)
            await bot.start(token=self.token)


if __name__ == '__main__':
    try:
        launcher = Launcher()
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        print('R.Sharp is now disconnected (keyboard interrupt)')
