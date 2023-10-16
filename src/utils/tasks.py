import asyncio
import logging
import time


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
