import disnake
import os
import logging
from disnake.ext import commands
from misc import collections
import math
from config.config_loader import config_file
from utils.messages import send_notification, NotificationType
from utils import tasks
from utils.string_format import seconds_to_string
from utils.language import get_str


class ErisProtectBot(commands.AutoShardedInteractionBot):
    instance = None

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

        if ErisProtectBot.instance is None:
            ErisProtectBot.instance = self

    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(activity=disnake.Game(config_file.get('GITHUB_URL')))

        collections.bot_stats.set_value(
            0,
            'shard-count',
            math.ceil(len(self.guilds) / int(config_file.get('GUILDS_PER_SHARD')))
        )

        self.loop.create_task(tasks.clear_temp_dictionaries(self))
        self.loop.create_task(tasks.check_temporary_punishments())
        self.loop.create_task(tasks.check_punishment_tasks())
        self.loop.create_task(tasks.apply_mute_role_permissions_task())

    async def on_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, exception
    ):
        if isinstance(exception, EmbedableError):
            await send_notification(
                inter,
                NotificationType.EmbedError,
                str(exception)
            )
        elif isinstance(exception, commands.CommandOnCooldown):
            await send_notification(
                inter,
                NotificationType.EmbedError,
                get_str(inter.guild, 'ERROR_COMMAND_ON_COOLDOWN',
                        retry_after=seconds_to_string(int(exception.retry_after), inter.guild))
            )
        elif isinstance(exception, commands.MissingPermissions):
            await send_notification(
                inter,
                NotificationType.EmbedError,
                get_str(inter.guild, 'ERROR_COMMAND_MISSING_PERMS')
            )
        elif isinstance(exception, commands.UserNotFound):
            await send_notification(
                inter,
                NotificationType.EmbedError,
                get_str(inter.guild, 'M_ERROR_USER_NOT_FOUND')
            )
        elif isinstance(exception, commands.MemberNotFound):
            await send_notification(
                inter,
                NotificationType.EmbedError,
                get_str(inter.guild, 'M_ERROR_MEMBER_NOT_FOUND')
            )
        else:
            raise exception


class EmbedableError(commands.errors.CommandError):
    pass
