import disnake
from disnake.ext import commands
from utils.language import get_str
from utils.messages import send_notification, NotificationType


class NukeScoreSettingsCommands(commands.Cog):
    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.slash_command(name='nuke-score')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def nuke_score(self, inter: disnake.ApplicationCommandInteraction):
        """
        Manage nuke scores for each action {{CMD_NUKE_SCORE}}
        """

        from misc.interactions.misc.nuke_score import ValueChangeView

        if inter.author.id != inter.guild.owner_id:
            return await send_notification(
                inter,
                NotificationType.EmbedError,
                get_str(inter.guild, 'M_ERROR_NOT_SERVER_OWNER')
            )

        embed = ValueChangeView.get_embed(inter.guild)

        await inter.response.send_message(embed=embed, ephemeral=True, view=ValueChangeView(inter.guild))

    @commands.Cog.listener('on_button_click')
    async def on_button_click(self, inter: disnake.MessageInteraction):
        from misc.interactions.misc.nuke_score import SetThresholdModal

        view = disnake.ui.View.from_message(inter.message)

        if view is None:
            return

        for item in view.children:
            if not isinstance(item, disnake.ui.Button):
                continue

            if item.custom_id == 'set_nuke_score_threshold':
                return await inter.response.send_modal(SetThresholdModal(inter.guild))


def setup(bot: commands.AutoShardedInteractionBot):
    bot.add_cog(NukeScoreSettingsCommands(bot))
