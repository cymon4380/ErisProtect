import disnake
from utils.language import get_str
from enum import Enum
from misc.collections import whitelist


class AntiNukePermission(Enum):
    CreateChannels = 'create_channels'
    EditChannels = 'edit_channels'
    DeleteChannels = 'delete_channels'

    CreateRoles = 'create_roles'
    EditRoles = 'edit_roles'
    DeleteRoles = 'delete_roles'

    CreateWebhooks = 'create_webhooks'
    EditWebhooks = 'edit_webhooks'
    DeleteWebhooks = 'delete_webhooks'

    EditServer = 'edit_server'

    KickMembers = 'kick_members'
    BanMembers = 'ban_members'
    TimeoutMembers = 'timeout_members'


class AntiNukePermissions:
    def __init__(self, user_id: int, guild: disnake.Guild, permissions: dict[str, bool] = None):
        self.user_id = user_id
        self.guild = guild
        self.permissions = {}

        if permissions is None:
            permissions = {}

        for permission in AntiNukePermission:
            overrided_permission = permissions.get(permission.value)
            self.permissions[permission.value] = overrided_permission if overrided_permission is not None else False

        self.clear = self.clear_perms

    def clear_perms(self, save: bool = True):
        self.permissions = {perm: False for perm in self.permissions}

        if save:
            self.save()

    def grant_all(self, save: bool = True):
        self.permissions = {perm: True for perm in self.permissions}

        if save:
            self.save()

    def save(self):
        if self.count_permissions() > 0:
            whitelist.set_values(self.guild.id, {str(self.user_id): self.permissions})
        else:
            whitelist.delete_key(self.guild.id, str(self.user_id))

    def has_permissions(self, *perms: AntiNukePermission) -> bool:
        if self.user_id == self.guild.owner_id or self.user_id == self.guild.me.id:
            return True

        for perm in perms:
            if self.permissions[perm.value]:
                return True

        return False

    def count_permissions(self) -> int:
        return len([v for v in self.permissions.values() if v])

    @staticmethod
    def from_database(user_id: int, guild: disnake.Guild):
        return AntiNukePermissions(user_id, guild, whitelist.get_value(guild.id, str(user_id)))

    @staticmethod
    def get_display_name(guild: disnake.Guild, permission: AntiNukePermission) -> str:
        return get_str(guild, f'F_PERM_{permission.value.upper()}')

    @staticmethod
    def get_permission_by_display_name(guild: disnake.Guild, display_name: str) -> AntiNukePermission:
        for permission in AntiNukePermission:
            if AntiNukePermissions.get_display_name(guild, permission) == display_name:
                return permission
