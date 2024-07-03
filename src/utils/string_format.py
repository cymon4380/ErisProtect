import disnake
import typing
import re
from disnake.ext import commands
from utils.language import get_str


def get_user_or_id(bot: commands.AutoShardedInteractionBot, user_id: int) -> typing.Union[disnake.User, int]:
    user = bot.get_user(user_id)

    if user is not None:
        return user
    return user_id


def string_to_seconds(string: str) -> int:
    units = {
        'y г л': 31557600,
        'mo мес': 2629800,
        'w н': 604800,
        'd д': 86400,
        'h ч': 3600,
        'm м': 60,
        's с': 1
    }

    total_seconds = 0
    parts = re.findall(r'\d+\s?[a-zа-я]+', string.lower())

    for part in parts:
        seconds = 0
        matched = False
        for s in re.split(r'(\d+)', part):
            s = s.strip()
            if len(s) == 0:
                continue

            if s.isdigit():
                seconds = int(s)
            else:
                for unit_list, value in units.items():
                    for unit in unit_list.split():
                        if not s.startswith(unit):
                            continue

                        seconds *= value
                        matched = True

                    if matched:
                        break

        total_seconds += seconds

    return total_seconds


def seconds_to_string(total_seconds: int, guild: disnake.Guild = None, separator: str = ' ') -> str:
    units = {
        'Y': 31557600,
        'MO': 2629800,
        'W': 604800,
        'D': 86400,
        'H': 3600,
        'MIN': 60,
        'S': 1
    }

    unit_list = list(units.keys())
    unit_sequence = []

    for unit, value in units.items():
        if unit_list.index(unit) != 0:
            previous_unit_value = units[unit_list[unit_list.index(unit) - 1]]
            unit_count = total_seconds % previous_unit_value // value
        else:
            unit_count = total_seconds // value

        if unit_count == 0:
            continue

        unit_sequence.append(str(unit_count) + (get_str(guild, unit) if guild is not None else unit.lower()))

    return separator.join(unit_sequence)
