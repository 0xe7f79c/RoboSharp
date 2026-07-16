import asyncio

from util.config import Config

from core.bot import RSharp

VANITY = r"""
 
    _
   / \
  /() \       _           _____ _               /\    
 |  __ \     | |         / ____| |             /  \    
 | |__) |___ | |__   ___| (___ | |__   __ _ _ / () \   
 |  _  // _ \| '_ \ / _ \\___ \| '_ \ / _` | '__| '_ \ 
 | | \ \ (_) | |_) | (_) |___) | | | | (_| | |  | |_) |
 |_|  \_\___/|_.__/ \___/_____/|_| |_|\__,_|_|  | .__/ 
                                                | |    
                                                |_|    
"""


class Launcher:
    def __init__(self) -> None:
        config = Config()
        self.token = config.token
        self.prefix = config.prefix
        self.pg_dsn = config.pg_dsn
        self.remove_old_help = config.remove_default_help

        self.bot = RSharp(self.prefix)

    async def run(self) -> None:
        print(VANITY)
        async with self.bot as bot:
            if self.remove_old_help:
                bot.remove_command('help')

            await self.bot.load_extension('cogs.help')
            await bot.start(token=self.token)


if __name__ == '__main__':
    launcher = Launcher()
    asyncio.run(launcher.run())
