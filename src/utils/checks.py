import logging
import disnake
import typing
import asyncio
from config.config_loader import config_file
from models.whitelist import AntiNukePermission, AntiNukePermissions
from utils.language import get_str


def is_bot_owner(user: typing.Union[disnake.User, disnake.Member, int]) -> bool:
    if not isinstance(user, int):
        user = user.id
    return user in config_file.get('OWNER_IDS')


async def check_antinuke(guild: disnake.Guild, permission: AntiNukePermission, skip_check: bool = False):
    from models.nuke_score import AntiNukeGuildData, NukeThreshold
    from models.antinuke import AntiNukeEntry, get_last_audit_log_user

    user = await get_last_audit_log_user(guild)
    guild_data = AntiNukeGuildData.get(guild)

    if not skip_check:
        perms = AntiNukePermissions.from_database(user.id, guild)

        if perms.has_permissions(permission):
            return

    threshold = NukeThreshold.get(guild)
    score = guild_data.get_score(permission)

    if score < threshold:
        return

    try:
        await user.ban(
            reason=f"{get_str(guild, 'M_ANTINUKE')}: {AntiNukePermissions.get_display_name(guild, permission)}"
        )
        logging.debug(
            f"{user} ({user.id}) was banned by anti-nuke system. Score: {score}/{threshold}. Permission: {permission}. "
            + f"Guild: {guild.name} ({guild.id})"
        )
    except AttributeError:
        pass
    except Exception as e:
        logging.error(
            f"Anti-nuke system could not ban {user} ({user.id}). Score: {score}/{threshold}. Permission: {permission}. "
            + f"Guild: {guild.name} ({guild.id}). Exception: {e}"
        )

    ignore = False
    if isinstance(user, disnake.Member):
        if guild.me.top_role <= user.top_role:
            ignore = True

    await asyncio.sleep(8)
    await AntiNukeEntry.recover_all(
        guild,
        ignore_guild=ignore
    )
