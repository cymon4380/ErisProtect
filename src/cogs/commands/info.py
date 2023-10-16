import disnake
from disnake.ext import commands
from misc.colors import Color
from utils.language import get_str
from config.config_loader import config_file


class InfoCommands(commands.Cog):
    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.slash_command(name='info')
    @commands.guild_only()
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        """
        Information about the bot {{CMD_INFO}}
        """

        embed = disnake.Embed(title=get_str(inter.guild, 'C_INFO_TITLE'), color=Color.primary)
        embed.description = get_str(inter.guild, 'M_INFO_BOT_DESC')
        
        embed.add_field(name=get_str(inter.guild, 'F_INFO_GUILDS_TOTAL'), value=len(self.bot.guilds))
        embed.add_field(name=get_str(inter.guild, 'F_INFO_USERS_TOTAL'),
                        value=len([u for u in self.bot.get_all_members() if not u.bot]))
        embed.add_field(name=get_str(inter.guild, 'F_SHARDS'), value=len(self.bot.shards))
        embed.add_field(name=get_str(inter.guild, 'F_INFO_YOUR_SHARD'), value=inter.guild.shard_id)
        embed.add_field(name=get_str(inter.guild, 'F_INFO_AVERAGE_LATENCY'),
                        value=f'{round(self.bot.latency * 1000, 2)} {get_str(inter.guild, "MS")}')

        github_btn = disnake.ui.Button(style=disnake.ButtonStyle.url, label='GitHub', url=config_file.get('GITHUB_URL'))

        await inter.response.send_message(embed=embed, components=[github_btn], ephemeral=True)


def setup(bot):
    bot.add_cog(InfoCommands(bot))
