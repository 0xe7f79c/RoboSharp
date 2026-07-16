from discord.ext import commands


class RContext(commands.Context):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
