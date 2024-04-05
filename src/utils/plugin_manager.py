from misc import collections
from disnake.ext import commands
import json
from os import getcwd, path, walk
import logging


class Plugin:
    def __init__(self, bot: commands.AutoShardedInteractionBot, _id: str):
        self.path = path.join(getcwd(), 'plugins', _id)

        with open(path.join(self.path, 'plugin.json'), 'r') as f:
            self.data = json.load(f)

        self.bot = bot
        self.id = _id
        self.enabled = collections.plugins.get_value(_id, 'enabled', self.data['ENABLED_BY_DEFAULT'])
        self.disabled_until = collections.plugins.get_value(_id, 'disabled-until', 0)
        self.name = self.data.get('NAME')
        self.description = self.data.get('DESCRIPTION')

        if self.description is not None:
            if len(self.description) == 0:
                self.description = None

    def __str__(self):
        return self.id

    def load(self):
        self.bot.load_extensions(path.join(self.path, 'cogs'))

        for address, dirs, files in walk(path.join(self.path, 'cogs')):
            for obj in files:
                if not obj.endswith('.py'):
                    continue

                _path = path.relpath(path.join(address, obj[:-3]), getcwd())

                self.bot.load_extension(_path.replace('/', '.').replace('\\', '.'))

    def enable(self):
        self.load()
        self.enabled = True
        collections.plugins.set_value(self.id, 'enabled', self.enabled)

    def disable(self):
        for address, dirs, files in walk(path.join(self.path, 'cogs')):
            for obj in files:
                if not obj.endswith('.py'):
                    continue

                _path = path.relpath(path.join(address, obj[:-3]), getcwd())

                self.bot.unload_extension(_path.replace('/', '.').replace('\\', '.'))

        self.enabled = False
        collections.plugins.set_value(self.id, 'enabled', self.enabled)

    def reload(self):
        for address, dirs, files in walk(path.join(self.path, 'cogs')):
            for obj in files:
                if not obj.endswith('.py'):
                    continue

                _path = path.relpath(path.join(address, obj[:-3]), getcwd())

                self.bot.reload_extension(_path.replace('/', '.').replace('\\', '.'))


def load_plugins(bot: commands.AutoShardedInteractionBot):
    for plugin in get_plugins(bot):
        if plugin.enabled:
            plugin.load()
            logging.debug(f"Plugin {plugin} loaded")


def get_plugins(bot: commands.AutoShardedInteractionBot) -> list[Plugin]:
    plugins = []

    for _, dirs, _ in walk(path.join(getcwd(), 'plugins')):
        for directory in dirs:
            try:
                plugin = Plugin(bot, directory)
                plugins.append(plugin)
            except FileNotFoundError:
                pass
            except KeyError:
                pass

    return plugins
