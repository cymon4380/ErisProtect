import disnake
import time
import asyncio
from enum import Enum
from models.bot import ErisProtectBot
from misc.collections import punishment_entries, punishment_tasks
from typing import Union
from uuid import uuid4
from utils.moderation import get_mute_role, apply_mute_role_permissions, find_user


class PunishmentType(Enum):
    Mute = 'mute'
    Timeout = 'timeout'
    Kick = 'kick'
    Ban = 'ban'


class PunishmentEntry:
    def __init__(
            self,
            guild: disnake.Guild,
            user_id: int,
            punishment_type: PunishmentType,
            created_at: float = None,
            _id: str = None,
            duration: int = None,
            reason: str = None
    ):
        self.id = _id or str(uuid4())
        self.guild = guild
        self.user_id = user_id
        self.punishment_type = punishment_type
        self.created_at = created_at or time.time()
        self.duration = duration
        self.reason = reason

    def active_until(self) -> float:
        return (self.created_at + self.duration) if self.duration is not None else -1

    async def revoke(self, delay: float = None):
        if delay is not None:
            await asyncio.sleep(delay)

        member = self.guild.get_member(self.user_id)

        match self.punishment_type:
            case PunishmentType.Mute:
                if member is not None:
                    role = await get_mute_role(self.guild, False)
                    if role is not None:
                        await member.remove_roles(role)

            case PunishmentType.Timeout:
                if member is not None:
                    await member.timeout(duration=0)

            case PunishmentType.Kick:
                raise InvalidPunishmentTypeError()

            case PunishmentType.Ban:
                async for entry in self.guild.bans():
                    if entry.user.id == self.user_id:
                        await self.guild.unban(entry.user)
                        break

        punishment_entries.delete_document(self.id)

    async def execute(self):
        member = self.guild.get_member(self.user_id)

        match self.punishment_type:
            case PunishmentType.Mute:
                if member is None:
                    raise MemberNotFoundError(self.user_id)

                role = await get_mute_role(self.guild)
                await member.add_roles(role, reason=self.reason)
                ErisProtectBot.instance.loop.create_task(apply_mute_role_permissions(role))

                if self.duration is not None:
                    ErisProtectBot.instance.loop.create_task(self.revoke(self.duration))

            case PunishmentType.Timeout:
                if member is None:
                    raise MemberNotFoundError(self.user_id)

                await member.timeout(duration=self.duration, reason=self.reason)

            case PunishmentType.Kick:
                await member.kick(reason=self.reason)

            case PunishmentType.Ban:
                await self.guild.ban(ErisProtectBot.instance.get_user(self.user_id), reason=self.reason)
                if self.duration is not None:
                    ErisProtectBot.instance.loop.create_task(self.revoke(self.duration))

    def save(self):
        if self.punishment_type == PunishmentType.Kick:
            return

        data = {
            '_id': self.id,
            'guild-id': self.guild.id,
            'user-id': self.user_id,
            'punishment-type': self.punishment_type.value,
            'duration': self.duration,
            'created-at': self.created_at,
            'reason': self.reason
        }

        punishment_entries.set_values(self.id, data)
        return data

    @staticmethod
    def deserialize(
            data: dict,
            guild: disnake.Guild = None,
            user_id: int = None,
            punishment_type: PunishmentType = None
    ):
        if punishment_type is None:
            for punishment in PunishmentType:
                if punishment.value == data.get('punishment-type'):
                    punishment_type = punishment

        entry = PunishmentEntry(
            _id=data.get('_id'),
            guild=guild or ErisProtectBot.instance.get_guild(data.get('guild-id')),
            user_id=user_id or data.get('user-id'),
            punishment_type=punishment_type,
            created_at=data.get('created-at'),
            duration=data.get('duration'),
            reason=data.get('reason')
        )

        return entry

    @staticmethod
    def get(_id: str):
        return PunishmentEntry.deserialize(punishment_entries.get_document(_id))

    @staticmethod
    def find(guild: disnake.Guild, user: Union[disnake.User, disnake.Member, int], punishment_type: PunishmentType):
        if isinstance(user, disnake.User) or isinstance(user, disnake.Member):
            _user = user.id
        else:
            _user = user

        data = punishment_entries.find_one({
            'guild-id': guild.id,
            'user-id': _user,
            'punishment-type': punishment_type.value
        })

        return PunishmentEntry.deserialize(data) if data is not None else None


class PunishmentTask:
    def __init__(
            self,
            guild: disnake.Guild,
            user: Union[disnake.User, str, int],
            punishment_type: PunishmentType,
            created_at: float = None,
            _id: str = None,
            duration: int = None,
            reason: str = None
    ):
        self.id = _id or str(uuid4())
        self.guild = guild
        self.user = user
        self.punishment_type = punishment_type
        self.created_at = created_at or time.time()
        self.duration = duration
        self.reason = reason

    def active_until(self) -> float:
        return (self.created_at + self.duration) if self.duration is not None else -1

    def revoke(self):
        punishment_tasks.delete_document(self.id)

    async def execute(self):
        user = find_user(self.user)
        if user is None:
            return

        entry = PunishmentEntry.find(self.guild, user, self.punishment_type)
        if entry is None:
            entry = PunishmentEntry(self.guild, user.id, self.punishment_type,
                                    duration=self.duration, reason=self.reason)
        else:
            entry.created_at = self.created_at
            entry.duration = self.duration
            entry.reason = self.reason

        await entry.execute()
        entry.save()
        self.revoke()

    def save(self):
        if isinstance(self.user, disnake.User) or isinstance(self.user, disnake.Member):
            user = self.user.id
        else:
            user = self.user

        data = {
            '_id': self.id,
            'guild-id': self.guild.id,
            'user': user,
            'punishment-type': self.punishment_type.value,
            'duration': self.duration,
            'created-at': self.created_at,
            'reason': self.reason
        }

        punishment_tasks.set_values(self.id, data)
        return data

    @staticmethod
    def deserialize(
            data: dict,
            guild: disnake.Guild = None,
            user: Union[str, int] = None,
            punishment_type: PunishmentType = None
    ):
        if punishment_type is None:
            for punishment in PunishmentType:
                if punishment.value == data.get('punishment-type'):
                    punishment_type = punishment

        task = PunishmentTask(
            _id=data.get('_id'),
            guild=guild or ErisProtectBot.instance.get_guild(data.get('guild-id')),
            user=user or data.get('user'),
            punishment_type=punishment_type,
            created_at=data.get('created-at'),
            duration=data.get('duration'),
            reason=data.get('reason')
        )

        return task

    @staticmethod
    def get(_id: str):
        return PunishmentTask.deserialize(punishment_tasks.get_document(_id))

    @staticmethod
    def find(guild: disnake.Guild, user: Union[disnake.User, disnake.Member, str, int], punishment_type: PunishmentType):
        user = user.id if isinstance(user, disnake.User) or isinstance(user, disnake.Member) else user

        data = punishment_tasks.find_one({
            'guild-id': guild.id,
            'user': user,
            'punishment-type': punishment_type.value
        })

        return PunishmentTask.deserialize(data) if data is not None else None


class MemberNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class InvalidPunishmentTypeError(Exception):
    pass
