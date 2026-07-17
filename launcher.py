import asyncio

import core

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


class Launcher:
    def __init__(self) -> None:
        config = core.Config()
        self.token = config.token
        self.prefix = config.prefix
        self.pg_dsn = config.pg_dsn
        self.remove_old_help = config.remove_default_help

        self.bot = core.RSharp(self.prefix)

    async def run(self) -> None:
        async with self.bot as bot, core.LogHandler(log_type='discord.http') as logger:
            bot.log_handler = logger
            bot.logger = bot.log_handler.logger

            lines: list[str] = VANITY.splitlines()
            for line in lines:
                bot.logger.info(line)

            if self.remove_old_help:
                bot.logger.info('Uninstalling default help...')
                bot.remove_command('help')
                bot.logger.warning(
                    f'Default {self.prefix}help command removed. You may need to register your own.'
                )

            await self.bot.load_extension('cogs.help')
            await self.bot.load_extension('cogs.admin')

            await bot.start(token=self.token)


if __name__ == '__main__':
    try:
        launcher = Launcher()
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        print('R.Sharp is now disconnected (keyboard interrupt)')
