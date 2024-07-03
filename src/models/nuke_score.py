import disnake
import time
import typing
from misc.collections import nuke_scores
from models.whitelist import AntiNukePermission
from utils.checks import check_antinuke


class NukeScoreEntry:
    def __init__(
            self,
            guild: disnake.Guild,
            permission: AntiNukePermission,
            value: int = None,
            cooldown: int = None,
    ):
        self.guild = guild
        self.permission = permission

        if value is not None:
            if value < 0:
                raise ValueError('Score entry value must not be less than 0.')

            self.value = value
        else:
            self.value = 1

        if cooldown is not None:
            if cooldown < 0:
                raise ValueError('Cooldown must not be less than 0.')

            self.cooldown = cooldown
        else:
            self.cooldown = 20

    @staticmethod
    def from_database(permission: AntiNukePermission, guild: disnake.Guild):
        permission_dict = nuke_scores.get_value(guild.id, permission.value, {})

        value = permission_dict.get('value')
        cooldown = permission_dict.get('cooldown')

        return NukeScoreEntry(
            guild=guild,
            permission=permission,
            value=value,
            cooldown=cooldown,
        )

    def save(self):
        nuke_scores.set_values(
            self.guild.id,
            {
                self.permission.value: {
                    'value': self.value,
                    'cooldown': self.cooldown,
                }
            }
        )


class NukeThreshold:
    @staticmethod
    def get(guild: typing.Union[disnake.Guild, int]) -> int:
        guild_id = guild.id if isinstance(guild, disnake.Guild) else guild

        return nuke_scores.get_value(guild_id, 'threshold', 10)

    from_database = get


class NukeAction:
    def __init__(
            self,
            guild: disnake.Guild,
            _type: AntiNukePermission,
            created_at: float = None
    ):
        self.guild = guild
        self.type = _type
        self.created_at = created_at or time.time()

    def is_expired(self, delete_if_expired: bool = True) -> bool:
        entry = NukeScoreEntry.from_database(self.type, self.guild)

        if time.time() - self.created_at > entry.cooldown:
            if delete_if_expired:
                data = AntiNukeGuildData.get(self.guild)
                data.actions.pop(data.actions.index(self))
            return True

        return False


class AntiNukeGuildData:
    def __init__(self, guild: disnake.Guild, actions: list[NukeAction] = None):
        self.guild = guild
        self.actions = actions or []

    def save(self):
        from main import bot

        bot.antinuke_guild_actions[self.guild.id] = self

    async def add_action(self, _type: AntiNukePermission, user: disnake.User = None):
        action = NukeAction(self.guild, _type)

        self.actions.append(action)
        self.save()
        await check_antinuke(self.guild, _type, _user=user)

    def get_score(self, _type: AntiNukePermission) -> int:
        entry = NukeScoreEntry.from_database(_type, self.guild)

        return len(
            [a for a in self.actions
             if a.type == _type
             and not a.is_expired()]
        ) * entry.value

    @staticmethod
    def get(guild: disnake.Guild):
        from main import bot

        for guild_id, data in bot.antinuke_guild_actions.items():
            if guild_id == guild.id:
                return data

        return AntiNukeGuildData(guild)
