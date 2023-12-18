import disnake
import os
import logging
from disnake.ext import commands
from misc import collections
import math
from config.config_loader import config_file
from utils.messages import send_notification, NotificationType
from utils import tasks


class ErisProtectBot(commands.AutoShardedInteractionBot):
    def __init__(self):
        intents = disnake.Intents.default()

        intents.members = True
        intents.message_content = True

        shard_count = collections.bot_stats.get_value(0, 'shard-count', 1)

        super().__init__(shard_count=shard_count, intents=intents)

        for address, dirs, files in os.walk(os.path.join(os.getcwd(), 'cogs')):
            self.load_extensions(address)

        self.i18n.load(os.path.join(os.getcwd(), 'lang_packs', 'slash_commands'))

        self.antinuke_entries = {}
        self.antinuke_guild_actions = {}
        self.ignored_guilds = {}    # If the bot can't punish a user

    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(activity=disnake.Game(config_file.get('GITHUB_URL')))

        collections.bot_stats.set_value(
            0,
            'shard-count',
            math.ceil(len(self.guilds) / int(config_file.get('GUILDS_PER_SHARD')))
        )

        self.loop.create_task(tasks.clear_temp_dictionaries(self))

    async def on_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, exception
    ):
        if isinstance(exception, EmbedableError):
            await send_notification(
                inter,
                NotificationType.EmbedError,
                str(exception)
            )
        else:
            raise exception


class EmbedableError(commands.errors.CommandError):
    pass
