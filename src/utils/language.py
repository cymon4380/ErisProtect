import disnake
import typing
import json
import os
import logging
from misc import collections


def get_guild_language(guild: typing.Union[disnake.Guild, int]) -> str:
    if isinstance(guild, disnake.Guild):
        guild = guild.id

    lang = collections.config.get_value(guild, 'language', 'en').lower()

    return lang


def get_str(guild: typing.Union[disnake.Guild, int], key: str, **kwargs) -> str:
    lang = get_guild_language(guild)
    key = key.upper()

    not_localized_warning = f'Not localized: {lang}/{key}'

    json_path = os.path.join(os.getcwd(), 'lang_packs', 'misc', lang + '.json')
    if not os.path.exists(json_path):
        logging.warning(not_localized_warning)
        return not_localized_warning

    with open(json_path, 'r', encoding='utf-8') as f:
        file = json.load(f)

    string = file.get(key)
    if string is None:
        logging.warning(not_localized_warning)
        return not_localized_warning

    for name, value in kwargs.items():
        string = string.replace('{{' + name + '}}', str(value))

    return string
