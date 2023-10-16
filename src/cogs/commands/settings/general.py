import disnake
from disnake.ext import commands
from misc.colors import Color
from misc.interactions.dropdowns.language_select import LanguageSelectView
from utils.language import get_str


class GeneralSettingsCommands(commands.Cog):
    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.slash_command(name='language')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def language(self, inter: disnake.ApplicationCommandInteraction):
        """
        Change the language of the bot {{CMD_LANGUAGE}}
        """

        embed = disnake.Embed(title=get_str(inter.guild, 'C_LANGUAGE_TITLE'), color=Color.primary)
        embed.description = get_str(inter.guild, 'M_LANGUAGE_DESC')
        embed.description += f'\n{get_str(inter.guild, "M_LANGUAGE_CURRENT")}: '
        embed.description += f'`{get_str(inter.guild, "L_NAME")}`'

        embed.set_footer(text=get_str(inter.guild, 'M_LANGUAGE_NOTE'))

        await inter.response.send_message(
            embed=embed,
            view=LanguageSelectView(),
            ephemeral=True
        )


def setup(bot):
    bot.add_cog(GeneralSettingsCommands(bot))
