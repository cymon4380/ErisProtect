import asyncio
import logging
import time
from misc.collections import punishment_entries, punishment_tasks
from utils.moderation import apply_mute_role_permissions, get_mute_role


async def clear_temp_dictionaries(bot, interval: float = 30):
    from models.antinuke import AntiNukeEntryState

    while True:
        try:
            for guild, entries in bot.antinuke_entries.items():
                for entry in entries:
                    if entry.state == AntiNukeEntryState.Recovered or time.time() > entry.expires:
                        bot.antinuke_entries[guild].pop(entries.index(entry))
                    elif entry.state == AntiNukeEntryState.ReadyToRecover:
                        if time.time() <= bot.ignored_guilds.get(guild, 0):
                            continue

                        try:
                            await entry.recover()
                        except Exception as e:
                            logging.error(e)

                if len(entries) == 0:
                    del bot.antinuke_entries[guild]

            for guild_id, timestamp in bot.ignored_guilds.items():
                if time.time() > timestamp:
                    del bot.ignored_guilds[guild_id]
        except Exception as e:
            logging.error(e)

        await asyncio.sleep(interval)


async def check_temporary_punishments(interval: float = 15):
    from models.moderation import PunishmentEntry, PunishmentType

    while True:
        try:
            for _id in list(punishment_entries.data.keys()):
                entry = PunishmentEntry.get(_id)
                if entry.punishment_type == PunishmentType.Kick:
                    continue

                if entry.active_until() != -1 and time.time() > entry.active_until():
                    await entry.revoke()

        except Exception as e:
            logging.error(e)

        await asyncio.sleep(interval)


async def check_punishment_tasks(interval: float = 15):
    from models.moderation import PunishmentTask

    while True:
        try:
            for _id in list(punishment_tasks.data.keys()):
                task = PunishmentTask.get(_id)
                if task.active_until() != -1 and time.time() > task.active_until():
                    task.revoke()
                    continue

                await task.execute()

        except Exception as e:
            logging.error(e)

        await asyncio.sleep(interval)


async def apply_mute_role_permissions_task(interval: float = 45):
    from models.bot import ErisProtectBot

    while True:
        try:
            for guild in ErisProtectBot.instance.guilds:
                role = await get_mute_role(guild, False)

                if role is None:
                    continue
                if punishment_entries.find_one({'guild-id': guild.id, 'punishment-type': 'mute'}) is None:
                    continue

                ErisProtectBot.instance.loop.create_task(apply_mute_role_permissions(role))

                await asyncio.sleep(5)
        except Exception as e:
            logging.error(e)

        await asyncio.sleep(interval)
