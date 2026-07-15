from enum import Enum
from typing import Callable, Optional
import discord
from discord.ext.commands import Bot
from discord.ui.button import Button
import discord.ui

NEXT_EMOJI = "\N{RIGHTWARDS BLACK ARROW}"
PREVIOUS_EMOJI = "\N{LEFTWARDS BLACK ARROW}"
STOP_EMOJI = "\N{OCTAGONAL SIGN}"


class Paginator(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.pages: dict[int, str] = {}
