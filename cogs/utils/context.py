from typing import TYPE_CHECKING, Any, Dict, Optional

import asyncpg
import discord
from discord import Guild
from discord.ext import commands

if TYPE_CHECKING:
    from cogs.admin import Admin

    from ...bot import RSharp


class ConfirmationEmbed(discord.Embed):
    def __init__(self, text: str = '', *, title=None, type: str = 'poll_result', url=None, timestamp=None):
        super().__init__(
            color=discord.Color.og_blurple(), title='Confirm', type=type, url=url, description=text, timestamp=timestamp
        )


class ConfirmView(discord.ui.View):
    def __init__(self, author_id: int, timeout: float = 20.0):
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("I didn't ask you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Yes', emoji='\N{WHITE HEAVY CHECK MARK}', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label='No', emoji='\N{CROSS MARK}', style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()


class RContext(commands.Context):
    bot: RSharp

    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        super().__init__(**kwargs)

    async def confirm(
        self,
        msg: str,
        title: str = 'Confirm?',
    ) -> Optional[bool]:
        """Sends a confirmation prompt. The visual result is an message
        with two emojis: \N{CROSS MARK}, and \N{WHITE HEAVY CHECK MARK}.
        Args:
            msg (str): The message to send to the user
            author_id (int): The ID of the author that sent the command.
        Returns:
            bool: True representing the authors choice of 'yes', False otherwise.
        """
        view = ConfirmView(author_id=self.author.id)
        message = await self.send(embed=ConfirmationEmbed(title=title, text=msg), view=view, ephemeral=True)
        await view.wait()
        return view.value

    async def default_role(self) -> discord.Role:
        """The guilds default role according to the bots records.

        Returns:
            discord.Role: The default role of the guild. If one wasn't created via command, will
            resort to the everyone role.
        """
        admin_cog: Admin = self.bot.get_cog('Admin')
        role = await admin_cog.get_default_role(self.guild.id)

        if role is None:
            return self.guild.default_role

        return role


class GuildContext(RContext):
    guild: Guild
    pool: asyncpg.Pool
    default_role: discord.Role
