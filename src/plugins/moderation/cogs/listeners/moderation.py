import disnake
import time
from disnake.ext import commands
from utils.moderation import get_mute_role
from models.moderation import PunishmentEntry, PunishmentType


class ModerationListeners(commands.Cog):
    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        entry = PunishmentEntry.find(member.guild, member, PunishmentType.Mute)
        if entry is None:
            return
        if entry.active_until() != -1 and time.time() >= entry.active_until():
            return

        await member.add_roles(await get_mute_role(member.guild), reason=entry.reason)


def setup(bot: commands.AutoShardedInteractionBot):
    bot.add_cog(ModerationListeners(bot))
