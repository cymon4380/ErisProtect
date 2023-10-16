import disnake
from disnake.ext import commands
import typing


def get_user_or_id(bot: commands.AutoShardedInteractionBot, user_id: int) -> typing.Union[disnake.User, int]:
    user = bot.get_user(user_id)

    if user is not None:
        return user
    return user_id
