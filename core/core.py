from logging import Logger

from discord.ext import commands

__all__ = ('SRC_LINK', 'UNKNOWN_EMOJI', 'Cog')


UNKNOWN_EMOJI = '\N{BLACK QUESTION MARK ORNAMENT}'
SRC_LINK = 'https://github.com/ps11n1/RoboSharp'


class Cog(commands.Cog, Logger):
    pictograph: str

    def __init_subclass__(
        cls,
        pictograph: str = 'UNKNOWN_EMOJI',
    ) -> None:
        """The meta-information for a given R. Sharp cog.

        Args:
            pictograph (str, optional): The pictograph (emoji) that identifies this cog.
            Defaults to 'UNKNOWN_EMOJI'.
        """
        super().__init_subclass__()
        cls.pictograph = pictograph

    def __init__(self) -> None:
        super().__init__()
