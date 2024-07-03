from disnake.ext import commands
from models.antinuke import *
from models.bot import ErisProtectBot
from models.nuke_score import AntiNukeGuildData
from models.whitelist import AntiNukePermission, AntiNukePermissions


class AntiNukeListeners(commands.Cog):
    def __init__(self, _bot: ErisProtectBot):
        self.bot = _bot

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel):
        guild = channel.guild
        target = channel
        permission = AntiNukePermission.DeleteChannels
        user = await get_last_audit_log_user(guild, disnake.AuditLogAction.channel_delete)

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        if isinstance(target, disnake.VoiceChannel) or isinstance(target, disnake.StageChannel):
            data = DamagedVoiceChannelData(target.id, guild, target, True)
        elif isinstance(target, disnake.CategoryChannel):
            data = DamagedCategoryChannelData(target.id, guild, target, True)
        elif isinstance(target, disnake.TextChannel) or isinstance(target, disnake.ForumChannel):
            data = DamagedTextChannelData(target.id, guild, target, True)
        else:
            return

        entry = AntiNukeEntry(
            target=target,
            data=data
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.abc.GuildChannel):
        guild = channel.guild
        target = channel
        permission = AntiNukePermission.CreateChannels

        user = None
        action = None
        async for entry in guild.audit_logs(limit=20):
            if entry.action == disnake.AuditLogAction.guild_update or\
                    (entry.action == disnake.AuditLogAction.channel_create and entry.target == channel):
                user = entry.user
                action = entry.action
                break

        if user is None or action is None:
            return

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=target,
            data=ExtraObjectData(target.id, guild, target)
        )

        entry.save()

        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: disnake.abc.GuildChannel, after: disnake.abc.GuildChannel):
        guild = after.guild
        target = before
        permission = AntiNukePermission.EditChannels
        user = await get_last_audit_log_user(guild, disnake.AuditLogAction.channel_update)

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        if isinstance(target, disnake.VoiceChannel) or isinstance(target, disnake.StageChannel):
            data = DamagedVoiceChannelData(target.id, guild, target, False)
        elif isinstance(target, disnake.CategoryChannel):
            data = DamagedCategoryChannelData(target.id, guild, target, False)
        elif isinstance(target, disnake.TextChannel) or isinstance(target, disnake.ForumChannel):
            data = DamagedTextChannelData(target.id, guild, target, False)
        else:
            return

        entry = AntiNukeEntry(
            target=target,
            data=data
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: disnake.Role):
        guild = role.guild
        target = role

        if target.is_integration() or target.managed:
            return

        permission = AntiNukePermission.DeleteRoles
        user = await get_last_audit_log_user(guild, disnake.AuditLogAction.role_delete)

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=target,
            data=DamagedRoleData(target.id, guild, target, True)
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role):
        guild = role.guild
        target = role

        if target.is_integration() or target.managed:
            return

        permission = AntiNukePermission.CreateRoles
        user = await get_last_audit_log_user(guild, disnake.AuditLogAction.role_create)

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=target,
            data=ExtraObjectData(target.id, guild, target)
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: disnake.Role, after: disnake.Role):
        guild = after.guild
        target = before
        permission = AntiNukePermission.EditRoles
        user = await get_last_audit_log_user(guild, disnake.AuditLogAction.role_update)

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=target,
            data=DamagedRoleData(target.id, guild, target, False)
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: disnake.abc.GuildChannel):
        guild = channel.guild
        entry = None
        async for audit_entry in guild.audit_logs(limit=20):
            if audit_entry.action in [
                disnake.AuditLogAction.webhook_create,
                disnake.AuditLogAction.webhook_update,
                disnake.AuditLogAction.webhook_delete
            ]:
                entry = audit_entry
                break

        if entry is None:
            return

        user = entry.user

        match entry.action:
            case disnake.AuditLogAction.webhook_create:
                permission = AntiNukePermission.CreateWebhooks
            case disnake.AuditLogAction.webhook_update:
                permission = AntiNukePermission.EditWebhooks
            case _:
                permission = AntiNukePermission.DeleteWebhooks

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        if permission is not None:
            await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: disnake.Guild, member: disnake.Member):
        target = member

        permission = AntiNukePermission.BanMembers
        user = await get_last_audit_log_user(guild, disnake.AuditLogAction.ban)

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=target,
            data=PunishedUserData(target.id, guild, target, PunishmentType.Ban)
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        guild = member.guild
        target = member

        permission = AntiNukePermission.KickMembers
        entry = None
        async for audit_entry in guild.audit_logs(limit=1):
            if audit_entry.action != disnake.AuditLogAction.kick:
                return
            entry = audit_entry

        if entry is None:
            return
        user = entry.user

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=target,
            data=PunishedUserData(target.id, guild, target, PunishmentType.Kick)
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        guild = after.guild
        target = before

        if after.current_timeout is None:
            return
        if before.current_timeout is not None:
            return
        if before.current_timeout == after.current_timeout:
            return

        permission = AntiNukePermission.TimeoutMembers
        entry = None
        async for audit_entry in guild.audit_logs(limit=1):
            if audit_entry.action != disnake.AuditLogAction.member_update:
                return
            entry = audit_entry

        if entry is None:
            return
        user = entry.user

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=target,
            data=PunishedUserData(target.id, guild, target, PunishmentType.Timeout)
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_guild_update(self, before: disnake.Guild, after: disnake.Guild):
        guild = before
        target = after
        permission = AntiNukePermission.EditServer
        user = await get_last_audit_log_user(guild, disnake.AuditLogAction.guild_update)

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=target,
            data=DamagedGuildData(guild)
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if '@everyone' in message.content:
            permission = AntiNukePermission.MentionEveryone
        elif '@here' in message.content:
            permission = AntiNukePermission.MentionHere
        else:
            return

        user = message.author
        guild = message.guild
        if user.id == self.bot.user.id:
            return

        if AntiNukePermissions.from_database(user.id, guild).has_permissions(permission):
            return

        entry = AntiNukeEntry(
            target=message,
            data=ExtraObjectData(message.id, guild, message)
        )

        entry.save()
        await AntiNukeGuildData.get(guild).add_action(permission, user=user)


def setup(_bot):
    _bot.add_cog(AntiNukeListeners(_bot))
