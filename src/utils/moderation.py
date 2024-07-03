import disnake
import asyncio
from misc.collections import config
from typing import Union
from misc.colors import Color
from utils.language import get_str
from utils.string_format import seconds_to_string, get_user_or_id


async def get_mute_role(guild: disnake.Guild, create_if_not_exists: bool = True) -> Union[disnake.Role | None]:
    role_id = config.get_value(guild.id, 'mute-role')
    role = guild.get_role(role_id) if role_id is not None else None

    if role is None and create_if_not_exists:
        role = await guild.create_role(name='Muted', permissions=disnake.Permissions.none())
        config.set_value(guild.id, 'mute-role', role.id)

    return role


async def apply_mute_role_permissions(role: disnake.Role):
    disable_reactions = config.get_value(role.guild.id, 'mute-disable-reactions', True)

    for channel in role.guild.channels:
        if isinstance(channel, disnake.VoiceChannel):
            await channel.set_permissions(role, speak=False, use_soundboard=False, send_messages=False,
                                          add_reactions=False if disable_reactions else None, send_voice_messages=False,
                                          stream=False)
        else:
            await channel.set_permissions(role, send_messages=False, add_reactions=False if disable_reactions else None,
                                          create_private_threads=False, create_public_threads=False,
                                          create_forum_threads=False, send_messages_in_threads=False)

        await asyncio.sleep(.075)


def generate_entry_embed(
        entry,
        moderator: disnake.User,
        reason: str = None
) -> disnake.Embed:
    from models.moderation import PunishmentType
    from models.bot import ErisProtectBot

    title_lang_keys = {
        PunishmentType.Mute: 'T_MUTED',
        PunishmentType.Timeout: 'T_TIMED_OUT',
        PunishmentType.Kick: 'T_KICKED',
        PunishmentType.Ban: 'T_BANNED',
    }
    title_lang_key = title_lang_keys[entry.punishment_type]

    fields = {
        'F_USER': f"`{get_user_or_id(ErisProtectBot.instance, entry.user_id)}`",
        'F_MODERATOR': f"`{moderator}`"
    }

    if entry.duration is not None:
        fields['F_DURATION'] = f"`{seconds_to_string(entry.duration, entry.guild)}`"
        fields['F_PUNISHMENT_ACTIVE_UNTIL'] = f"<t:{int(entry.active_until())}:f>"

    fields['F_REASON'] = (reason or get_str(entry.guild, 'M_NO_REASON'))\
        .replace('@everyone', '@ever_one').replace('@here', '@h_re')

    fields['F_REASON'] = f"`{fields['F_REASON']}`"

    embed = disnake.Embed(title=get_str(entry.guild, title_lang_key), color=Color.primary)
    embed.description = '\n'.join([f"**{get_str(entry.guild, name)}:** {value}" for name, value in fields.items()])

    return embed


def generate_task_embed(
        task,
        moderator: disnake.User,
        reason: str = None
) -> disnake.Embed:
    from models.moderation import PunishmentType

    type_lang_keys = {
        PunishmentType.Ban: 'F_BAN',
    }
    type_lang_key = type_lang_keys[task.punishment_type]

    fields = {
        'F_USER': f"`{task.user}`",
        'F_TYPE': f"`{get_str(task.guild, type_lang_key)}`",
        'F_MODERATOR': f"`{moderator}`"
    }

    if task.duration is not None:
        fields['F_DURATION'] = f"`{seconds_to_string(task.duration, task.guild)}`"

    fields['F_REASON'] = (reason or get_str(task.guild, 'M_NO_REASON'))\
        .replace('@everyone', '@ever_one').replace('@here', '@h_re')

    fields['F_REASON'] = f"`{fields['F_REASON']}`"

    embed = disnake.Embed(title=get_str(task.guild, 'T_TASK_CREATED'), color=Color.primary)

    embed.description = get_str(task.guild, 'M_TASK_CREATED_DESCRIPTION') + '\n\n'
    embed.description += '\n'.join([f"**{get_str(task.guild, name)}:** {value}" for name, value in fields.items()])

    return embed


def find_user(user: Union[disnake.User, str, int]) -> Union[disnake.User, disnake.Member, None]:
    from models.bot import ErisProtectBot

    if isinstance(user, disnake.User) or isinstance(user, disnake.Member):
        return user
    elif isinstance(user, str):
        if user.isdigit():
            return ErisProtectBot.instance.get_user(int(user))

        return disnake.utils.get(ErisProtectBot.instance.users, name=user)
    else:
        return ErisProtectBot.instance.get_user(user)
