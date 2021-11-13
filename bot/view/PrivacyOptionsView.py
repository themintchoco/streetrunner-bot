import nextcord

from bot.api.StreetRunnerApi.Player import Player
from bot.player.privacy import Privacy


class PrivacyOptionButton(nextcord.ui.Button):
    async def callback(self, interaction: nextcord.Interaction):
        await self.view.update(self, interaction)


class PrivacyOptionsView(nextcord.ui.View):
    def __init__(self, user: nextcord.User, privacy: Privacy):
        super().__init__(timeout=None)
        self._user = user
        self._privacy = privacy

        cats = {
            'Mines': Privacy.prison,
            'Arena': Privacy.arena,
            'Time Played': Privacy.time,
            'Balance': Privacy.balance,
        }

        for label, cat in cats.items():
            self.add_item(PrivacyOptionButton(
                label=label,
                custom_id=cat.name,
                style=nextcord.ButtonStyle.primary if cat.value & self._privacy else nextcord.ButtonStyle.secondary,
            ))

    async def update(self, button: PrivacyOptionButton, interaction: nextcord.Interaction):
        value = Privacy[button.custom_id]
        self._privacy ^= value
        button.style = nextcord.ButtonStyle.primary if value & self._privacy else nextcord.ButtonStyle.secondary

        await Player({'discord_id': self._user.id}).PlayerPrivacy().update({'value': self._privacy})
        await interaction.response.edit_message(view=self)

    async def interaction_check(self, interaction: nextcord.Interaction):
        return interaction.user == self._user
