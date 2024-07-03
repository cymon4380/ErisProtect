import logging
import time
import typing
import disnake
from config.config_loader import config_file
from main import bot
from enum import Enum
from utils.language import get_str


class AntiNukeEntryState(Enum):
    ReadyToRecover = 0
    Recovering = 1
    Recovered = 2


class PunishmentType(Enum):
    Timeout = 0
    Kick = 1
    Ban = 2


def get_category(guild: disnake.Guild, name: str, _id: int, position: int = 0) -> typing.Union[disnake.CategoryChannel, None]:
    if name is None or _id is None or position == 0:
        return

    id_category = guild.get_channel(_id)
    name_categories = [category for category in guild.categories if category.name == name]

    if id_category is not None:
        if isinstance(id_category, disnake.CategoryChannel):
            return id_category

    if len(name_categories) == 0:
        return
    if len(name_categories) < position:
        return name_categories[-1]

    return name_categories[position - 1]


async def get_last_audit_log_user(guild: disnake.Guild, action: disnake.AuditLogAction = None) -> disnake.Member:
    async for _action in guild.audit_logs(limit=1, action=action):
        if _action.user.id != guild.me.id:
            return _action.user

    return guild.me


class RecoverableData:
    def __init__(self, _id: int, guild: disnake.Guild):
        self.id = _id
        self.guild = guild


class AntiNukeEntry:
    def __init__(
            self,
            target,
            data: RecoverableData,
            state: AntiNukeEntryState = AntiNukeEntryState.ReadyToRecover,
            expires: float = None
    ):
        self.target = target
        self.data = data
        self.state = state
        self.expires = expires or time.time() + config_file.get('ENTRY_EXPIRATION_TIME', 600)

    def save(self):
        existing = AntiNukeEntry.get(_id=self.data.id, guild=self.data.guild)

        if existing is not None:
            index = bot.antinuke_entries[self.data.guild.id].index(existing)
            bot.antinuke_entries[self.data.guild.id][index] = self
        else:
            entries = bot.antinuke_entries.get(self.data.guild.id, [])
            entries.append(self)
            bot.antinuke_entries[self.data.guild.id] = entries

    @staticmethod
    def get(_id: int, guild: disnake.Guild):
        entries = bot.antinuke_entries.get(guild.id, [])

        for entry in entries:
            if entry.data.id == _id:
                return entry

    async def recover(self, force_recovery: bool = False):
        if self.state != AntiNukeEntryState.ReadyToRecover and not force_recovery:
            logging.debug(f"{self.target} ({self.target.id}): Already recovering/recovered, ignoring it.")
            return

        self.state = AntiNukeEntryState.Recovering
        self.save()

        if isinstance(self.target, disnake.TextChannel) and isinstance(self.data, DamagedTextChannelData):
            if self.data.is_deleted or not self.data.exists:
                await self.data.guild.create_text_channel(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    topic=self.data.topic,
                    slowmode_delay=self.data.slowmode_delay,
                    nsfw=self.data.nsfw,
                    category=get_category(
                        self.data.guild,
                        self.data.category_name,
                        self.data.category_id,
                        self.data.category_position
                    ),
                    overwrites=self.data.overwrites,
                    position=self.data.position
                )
            else:
                await self.target.edit(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    topic=self.data.topic,
                    slowmode_delay=self.data.slowmode_delay,
                    nsfw=self.data.nsfw,
                    category=get_category(
                        self.data.guild,
                        self.data.category_name,
                        self.data.category_id,
                        self.data.category_position
                    ),
                    overwrites=self.data.overwrites,
                    position=self.data.position
                )
        elif isinstance(self.target, disnake.ForumChannel) and isinstance(self.data, DamagedTextChannelData):
            if self.data.is_deleted or not self.data.exists:
                await self.data.guild.create_forum_channel(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    topic=self.data.topic,
                    slowmode_delay=self.data.slowmode_delay,
                    nsfw=self.data.nsfw,
                    category=get_category(
                        self.data.guild,
                        self.data.category_name,
                        self.data.category_id,
                        self.data.category_position
                    ),
                    overwrites=self.data.overwrites,
                    position=self.data.position,
                    available_tags=self.data.forum_tags
                )
            else:
                await self.target.edit(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    topic=self.data.topic,
                    slowmode_delay=self.data.slowmode_delay,
                    nsfw=self.data.nsfw,
                    category=get_category(
                        self.data.guild,
                        self.data.category_name,
                        self.data.category_id,
                        self.data.category_position
                    ),
                    overwrites=self.data.overwrites,
                    position=self.data.position,
                    available_tags=self.data.forum_tags
                )
        elif isinstance(self.target, disnake.VoiceChannel) and isinstance(self.data, DamagedVoiceChannelData):
            if self.data.is_deleted or not self.data.exists:
                await self.data.guild.create_voice_channel(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    position=self.data.position,
                    overwrites=self.data.overwrites,
                    nsfw=self.data.nsfw,
                    category=get_category(
                        self.data.guild,
                        self.data.category_name,
                        self.data.category_id,
                        self.data.category_position
                    ),
                    slowmode_delay=self.data.slowmode_delay,
                    bitrate=self.data.bitrate,
                    user_limit=self.data.user_limit
                )
            else:
                await self.target.edit(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    position=self.data.position,
                    overwrites=self.data.overwrites,
                    nsfw=self.data.nsfw,
                    category=get_category(
                        self.data.guild,
                        self.data.category_name,
                        self.data.category_id,
                        self.data.category_position
                    ),
                    slowmode_delay=self.data.slowmode_delay,
                    bitrate=self.data.bitrate,
                    user_limit=self.data.user_limit,
                )
        elif isinstance(self.target, disnake.StageChannel) and isinstance(self.data, DamagedVoiceChannelData):
            if self.data.is_deleted or not self.data.exists:
                await self.data.guild.create_stage_channel(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    position=self.data.position,
                    overwrites=self.data.overwrites,
                    nsfw=self.data.nsfw,
                    category=get_category(
                        self.data.guild,
                        self.data.category_name,
                        self.data.category_id,
                        self.data.category_position
                    ),
                    slowmode_delay=self.data.slowmode_delay,
                    bitrate=self.data.bitrate,
                    user_limit=self.data.user_limit
                )
            else:
                await self.target.edit(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    position=self.data.position,
                    overwrites=self.data.overwrites,
                    nsfw=self.data.nsfw,
                    category=get_category(
                        self.data.guild,
                        self.data.category_name,
                        self.data.category_id,
                        self.data.category_position
                    ),
                    slowmode_delay=self.data.slowmode_delay,
                    bitrate=self.data.bitrate,
                    user_limit=self.data.user_limit
                )
        elif isinstance(self.target, disnake.CategoryChannel) and isinstance(self.data, DamagedCategoryChannelData):
            if self.data.is_deleted or not self.data.exists:
                await self.data.guild.create_category(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    position=self.data.position,
                    overwrites=self.data.overwrites
                )
            else:
                await self.target.edit(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    position=self.data.position,
                    overwrites=self.data.overwrites
                )
        elif isinstance(self.target, disnake.Role) and isinstance(self.data, DamagedRoleData):
            if self.data.is_deleted or not self.data.exists:
                role = await self.data.guild.create_role(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    permissions=self.data.permissions,
                    color=self.data.color,
                    hoist=self.data.hoist,
                    mentionable=self.data.mentionable,
                )
                await role.edit(position=self.data.position)   # Why can't I specify the role position in create_role()?
            else:
                await self.target.edit(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name,
                    permissions=self.data.permissions,
                    color=self.data.color,
                    hoist=self.data.hoist,
                    mentionable=self.data.mentionable,
                    position=self.data.position
                )
        elif isinstance(self.target, disnake.Member) and isinstance(self.data, PunishedUserData):
            match self.data.punishment:
                case PunishmentType.Ban:
                    await self.data.guild.unban(self.target, reason=get_str(self.data.guild, 'M_ANTINUKE'))
                case PunishmentType.Timeout:
                    member = self.data.guild.get_member(self.target.id)
                    if member is not None:
                        await member.timeout(duration=None, reason=get_str(self.data.guild, 'M_ANTINUKE'))
        elif isinstance(self.target, disnake.Webhook) and isinstance(self.data, DamagedWebhookData):
            if self.data.is_deleted or not self.data.exists:
                await self.data.channel.create_webhook(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name
                )
            else:
                await self.target.edit(
                    reason=get_str(self.data.guild, 'M_ANTINUKE'),
                    name=self.data.name
                )
        elif isinstance(self.target, disnake.Guild) and isinstance(self.data, DamagedGuildData):
            await self.target.edit(
                reason=get_str(self.data.guild, 'M_ANTINUKE'),
                name=self.data.name
            )
        elif isinstance(self.data, ExtraObjectData):
            if not isinstance(self.target, disnake.Webhook):
                if isinstance(self.target, disnake.Message):
                    await self.target.delete()
                else:
                    await self.target.delete(reason=get_str(self.data.guild, 'M_ANTINUKE'))
            else:
                webhook = await self.target.fetch()
                await webhook.delete(reason=get_str(self.data.guild, 'M_ANTINUKE'))

        self.state = AntiNukeEntryState.Recovered
        self.save()

    @staticmethod
    async def recover_all(guild: disnake.Guild, force_recovery: bool = False, ignore_guild: bool = False):
        entries = bot.antinuke_entries.get(guild.id, [])

        if time.time() < bot.ignored_guilds.get(guild.id, 0) and not force_recovery:
            logging.debug(
                f"Guild {guild.name} ({guild.id}) is ignored, and force recovery is off. Aborting..."
            )
            return

        recovered = 0

        for step in range(1, 4):    # Step 4 is not included
            for entry in entries:
                if entry.state == AntiNukeEntryState.ReadyToRecover or force_recovery:
                    try:
                        if step == 1 and not isinstance(entry.data, DamagedRoleData):
                            continue
                        elif step == 2 and not isinstance(entry.data, DamagedCategoryChannelData):
                            continue

                        await entry.recover(force_recovery=force_recovery)
                        recovered += 1
                    except Exception as e:
                        logging.error(e)

        logging.debug(
            f"{guild.name} ({guild.id}): Recovered {recovered} items."
        )

        if ignore_guild:
            bot.ignored_guilds[guild.id] = time.time() + config_file.get('GUILD_IGNORING_DURATION', 180)
            logging.debug(
                f"{guild.name} ({guild.id}): Ignored."
            )


class DamagedTextChannelData(RecoverableData):
    def __init__(
            self,
            _id: int,
            guild: disnake.Guild,
            channel: typing.Union[disnake.TextChannel, disnake.ForumChannel],
            is_deleted: bool
    ):
        super().__init__(_id=_id, guild=guild)
        self.target = channel
        self.is_deleted = is_deleted
        self.exists = self.guild.get_channel(self.id) is not None

        self.name = channel.name
        self.overwrites = channel.overwrites
        self.topic = channel.topic
        self.nsfw = channel.nsfw
        self.slowmode_delay = channel.slowmode_delay
        self.position = channel.position
        self.category_id = channel.category_id
        self.category_name = channel.category.name if channel.category is not None else None
        self.category_position = channel.category.position if channel.category is not None else 0
        self.forum_tags = None if not isinstance(channel, disnake.ForumChannel) else channel.available_tags


class DamagedVoiceChannelData(RecoverableData):
    def __init__(
            self,
            _id: int,
            guild: disnake.Guild,
            channel: typing.Union[disnake.VoiceChannel, disnake.StageChannel],
            is_deleted: bool
    ):
        super().__init__(_id=_id, guild=guild)
        self.target = channel
        self.is_deleted = is_deleted
        self.exists = self.guild.get_channel(self.id) is not None

        self.name = channel.name
        self.overwrites = channel.overwrites
        self.bitrate = channel.bitrate
        self.user_limit = channel.user_limit
        self.nsfw = channel.nsfw
        self.slowmode_delay = channel.slowmode_delay
        self.position = channel.position
        self.category_id = channel.category_id
        self.category_name = channel.category.name if channel.category is not None else None
        self.category_position = channel.category.position if channel.category is not None else 0


class DamagedCategoryChannelData(RecoverableData):
    def __init__(
            self,
            _id: int,
            guild: disnake.Guild,
            channel: disnake.CategoryChannel,
            is_deleted: bool
    ):
        super().__init__(_id=_id, guild=guild)
        self.target = channel
        self.is_deleted = is_deleted
        self.exists = self.guild.get_channel(self.id) is not None

        self.name = channel.name
        self.overwrites = channel.overwrites
        self.nsfw = channel.nsfw
        self.position = channel.position


class DamagedRoleData(RecoverableData):
    def __init__(
            self,
            _id: int,
            guild: disnake.Guild,
            role: disnake.Role,
            is_deleted: bool
    ):
        super().__init__(_id=_id, guild=guild)
        self.target = role
        self.is_deleted = is_deleted
        self.exists = self.guild.get_role(self.id) is not None

        self.name = role.name
        self.color = role.color
        self.position = role.position
        self.mentionable = role.mentionable
        self.hoist = role.hoist
        self.permissions = role.permissions


class DamagedGuildData(RecoverableData):
    def __init__(self, guild: disnake.Guild):
        super().__init__(_id=guild.id, guild=guild)

        self.name = guild.name


class DamagedWebhookData(RecoverableData):
    def __init__(
            self,
            _id: int,
            guild: disnake.Guild,
            webhook: disnake.Webhook,
            is_deleted: bool
    ):
        super().__init__(_id=_id, guild=guild)
        self.target = webhook
        self.is_deleted = is_deleted
        self.exists = self.guild.get_role(self.id) is not None

        self.name = webhook.name
        self.channel = webhook.channel


class PunishedUserData(RecoverableData):
    def __init__(
            self,
            _id: int,
            guild: disnake.Guild,
            member: disnake.Member,
            punishment_type: PunishmentType
    ):
        super().__init__(_id=_id, guild=guild)

        self.target = member
        self.punishment = punishment_type


class ExtraObjectData(RecoverableData):
    def __init__(
            self,
            _id: int,
            guild: disnake.Guild,
            target
    ):
        super().__init__(_id=_id, guild=guild)

        self.target = target
