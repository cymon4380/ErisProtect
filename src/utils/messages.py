import disnake
from misc.colors import Color
from enum import Enum
from utils.language import get_str


class NotificationType(Enum):
    EmbedDone = ('M_DONE', Color.success)
    EmbedWarning = ('M_WARNING', Color.warning)
    EmbedError = ('M_ERROR', Color.danger)


def get_notification_embed(
        guild: disnake.Guild,
        notification_type: NotificationType,
        message: str,
        title: str = None
) -> disnake.Embed:
    if title is None:
        title = notification_type.value[0]

    embed = disnake.Embed(title=get_str(guild, title), description=message, color=notification_type.value[1])

    return embed


async def send_notification(
        inter: disnake.ApplicationCommandInteraction,
        notification_type: NotificationType,
        message: str,
        title: str = None,
        ephemeral: bool = True,
        delete_after: float = 300
):
    embed = get_notification_embed(inter.guild, notification_type, message, title)

    await inter.response.send_message(embed=embed, delete_after=delete_after, ephemeral=ephemeral)
