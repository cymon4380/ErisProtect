import disnake
from utils.language import get_str
from utils import plugin_manager
from misc.colors import Color
from disnake.ext import commands


class PluginManagerView(disnake.ui.View):
    def __init__(self, plugin: plugin_manager.Plugin, guild: disnake.Guild):
        self.plugin = plugin
        self.guild = guild
        super().__init__()
        self.update_state()

        self.enable_plugin.label = get_str(guild, 'A_ENABLE')
        self.disable_plugin.label = get_str(guild, 'A_DISABLE')
        self.reload_plugin.label = get_str(guild, 'A_RELOAD')
        self.back.label = get_str(guild, 'A_PLUGIN_MANAGER_BACK')

    def update_state(self):
        self.disable_plugin.disabled = not self.plugin.enabled
        self.enable_plugin.disabled = self.plugin.enabled
        self.reload_plugin.disabled = not self.plugin.enabled

    @disnake.ui.button(label='Enable', style=disnake.ButtonStyle.green)
    async def enable_plugin(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.plugin.enable()
        self.update_state()

        await inter.response.edit_message(embed=self.generate_embed(), view=self)

    @disnake.ui.button(label='Disable', style=disnake.ButtonStyle.red)
    async def disable_plugin(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.plugin.disable()
        self.update_state()

        await inter.response.edit_message(embed=self.generate_embed(), view=self)

    @disnake.ui.button(label='Reload', style=disnake.ButtonStyle.blurple)
    async def reload_plugin(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.plugin.reload()
        self.update_state()

        await inter.response.send_message(f"### ✅ {get_str(self.guild, 'M_PLUGIN_MANAGER_RELOADED')}", ephemeral=True)

    @disnake.ui.button(label='Back to plugin list', style=disnake.ButtonStyle.gray)
    async def back(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(
            embed=generate_plugin_list_embed(self.plugin.bot, self.guild),
            view=PluginSelectView(self.plugin.bot, self.guild)
        )

    def generate_embed(self) -> disnake.Embed:
        embed = disnake.Embed()
        embed.title = f"{get_str(self.guild, 'C_PLUGIN_MANAGER_TITLE')}: {self.plugin.name} (`{self.plugin}`)"
        embed.description = f"""
**{get_str(self.guild, 'M_DESCRIPTION')}:** `{self.plugin.description
        if self.plugin.description is not None else get_str(self.guild, 'M_NO_DESCRIPTION')}`

{get_str(self.guild, 'M_PLUGIN_MANAGER_ENABLED' if self.plugin.enabled else 'M_PLUGIN_MANAGER_DISABLED')}
"""
        embed.color = Color.success if self.plugin.enabled else Color.danger

        return embed


def generate_plugin_list_embed(bot: commands.AutoShardedInteractionBot, guild: disnake.Guild) -> disnake.Embed:
    plugins = plugin_manager.get_plugins(bot)
    enabled_plugins = [p for p in plugins if p.enabled]
    disabled_plugins = [p for p in plugins if not p.enabled]
    embed = disnake.Embed(color=Color.primary)
    embed.title = get_str(guild, 'C_PLUGIN_LIST_TITLE')

    embed.description = f"## {get_str(guild, 'M_PLUGIN_LIST_TOTAL_PLUGINS')}: `{len(plugins)}`"

    if len(enabled_plugins) > 0:
        embed.add_field(inline=False, name=f"{get_str(guild, 'M_PLUGIN_LIST_ENABLED_PLUGINS')} ({len(enabled_plugins)})",
                        value='\n'.join([f"{p.name} (`{p}`)" for p in enabled_plugins]))
    if len(disabled_plugins) > 0:
        embed.add_field(inline=False, name=f"{get_str(guild, 'M_PLUGIN_LIST_DISABLED_PLUGINS')} ({len(disabled_plugins)})",
                        value='\n'.join([f"{p.name} (`{p}`)" for p in disabled_plugins]))

    return embed


class PluginSelectMenu(disnake.ui.StringSelect):
    def __init__(self, bot: commands.AutoShardedInteractionBot, guild: disnake.Guild):
        self.bot = bot
        self.guild = guild

        options = []
        for plugin in plugin_manager.get_plugins(bot):
            options.append(disnake.SelectOption(
                label=plugin.id,
                description=f"{plugin.name} | {plugin.description if plugin.description else {get_str(guild, 'M_NO_DESCRIPTION')}}"
            ))

        super().__init__(placeholder=get_str(guild, 'D_PLUGIN_LIST_CHOOSE'), options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        view = PluginManagerView(plugin_manager.Plugin(self.bot, self.values[0]), self.guild)
        await inter.response.edit_message(embed=view.generate_embed(), view=view)


class PluginSelectView(disnake.ui.View):
    def __init__(self, bot: commands.AutoShardedInteractionBot, guild: disnake.Guild):
        super().__init__()

        self.add_item(PluginSelectMenu(bot, guild))
