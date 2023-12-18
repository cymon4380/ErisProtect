import disnake
from disnake.ext import commands
from models.bot import EmbedableError
from utils.language import get_str
from config.config_loader import config_file
from utils import checks
from misc.interactions.misc import plugin_manager


class ServiceCommands(commands.Cog):
    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.slash_command(name='cog', guild_ids=config_file.get('SERVICE_GUILDS'))
    @commands.guild_only()
    async def cog(
            self,
            inter: disnake.ApplicationCommandInteraction,
            cog: str,
            action: str = commands.Param(choices=[
                disnake.Localized('load', key='COG_OPTION_LOAD'),
                disnake.Localized('reload', key='COG_OPTION_RELOAD'),
                disnake.Localized('unload', key='COG_OPTION_UNLOAD')
            ])
    ):
        """
        Load, reload or unload a cog {{CMD_COG}}

        Parameters
        ----------
        cog: Cog to manage {{COG_COG}}
        action: Action to do {{COG_ACTION}}
        """

        if not checks.is_bot_owner(inter.author):
            return

        if not cog.startswith('cogs.'):
            cog = 'cogs.' + cog

        try:
            match action:
                case 'load':
                    self.bot.load_extension(cog)
                case 'reload':
                    self.bot.reload_extension(cog)
                case 'unload':
                    self.bot.unload_extension(cog)

            await inter.response.send_message(f'### ✅ {get_str(inter.guild, "M_DONE")}', ephemeral=True)
        except Exception as e:
            raise EmbedableError(str(e))

    @commands.slash_command(name='plugins', guild_ids=config_file.get('SERVICE_GUILDS'))
    @commands.guild_only()
    async def plugins(self, inter: disnake.ApplicationCommandInteraction):
        """
        Manage plugins {{CMD_PLUGINS}}
        """

        if not checks.is_bot_owner(inter.author):
            return

        await inter.response.send_message(
            embed=plugin_manager.generate_plugin_list_embed(self.bot, inter.guild),
            view=plugin_manager.PluginSelectView(self.bot, inter.guild),
            ephemeral=True
        )


def setup(bot: commands.AutoShardedInteractionBot):
    bot.add_cog(ServiceCommands(bot))
