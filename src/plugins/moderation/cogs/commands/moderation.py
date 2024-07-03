import time
import disnake
from disnake.ext import commands
from misc.colors import Color
from models.moderation import PunishmentEntry, PunishmentTask, PunishmentType
from models.bot import EmbedableError
from utils.language import get_str
from utils.string_format import string_to_seconds, get_user_or_id, seconds_to_string
from utils.moderation import generate_entry_embed, generate_task_embed, get_mute_role, apply_mute_role_permissions,\
    find_user
from misc.collections import config, punishment_entries, punishment_tasks
from misc.interactions.buttons.paginator import Paginator


class ModerationCommands(commands.Cog):
    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.slash_command(name='mute')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def mute(
            self,
            inter: disnake.ApplicationCommandInteraction,
            member: disnake.Member,
            duration: str = None,
            reason: str = None
    ):
        """
        Mute a user on the server {{CMD_MUTE}}

        Parameters
        ----------
        member: Member to mute {{MUTE_MEMBER}}
        duration: Duration (e.g. 1h30m) {{C_DURATION}}
        reason: Reason {{C_REASON}}
        """

        if member == inter.author:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_SELF'))
        if member == self.bot.user:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ME'))
        if member.guild_permissions.administrator:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ADMINISTRATOR'))

        if duration is not None:
            duration = string_to_seconds(duration)
            if duration <= 0:
                duration = None

        reason = reason or get_str(inter.guild, 'M_NO_REASON')

        entry = PunishmentEntry.find(inter.guild, member, PunishmentType.Mute)
        if entry is None:
            entry = PunishmentEntry(inter.guild, member.id, PunishmentType.Mute)

        entry.created_at = time.time()
        entry.duration = duration
        entry.reason = f"{inter.author}: {reason}"

        entry.save()
        await entry.execute()

        await inter.response.send_message(embed=generate_entry_embed(entry, inter.author, reason))

    @commands.slash_command(name='mute-role')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def mute_role(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role = None):
        """
        Set mute role {{CMD_MUTE_ROLE}}

        Parameters
        ----------
        role: Role to set {{MUTE_ROLE}}
        """

        if role is None:
            current_role = await get_mute_role(inter.guild, False)

            if current_role is None:
                return await inter.response.send_message(get_str(inter.guild, 'M_SET_MUTE_ROLE_SHOW_UNASSIGNED'),
                                                         ephemeral=True)

            return await inter.response.send_message(get_str(inter.guild, 'M_SET_MUTE_ROLE_SHOW',
                                                             role=current_role.mention), ephemeral=True)

        if inter.guild.me.top_role <= role:
            raise EmbedableError(get_str(inter.guild, 'ERROR_SET_MUTE_ROLE_TOP'))
        if role.managed:
            raise EmbedableError(get_str(inter.guild, 'ERROR_SET_MUTE_ROLE_MANAGED'))

        config.set_value(inter.guild.id, 'mute-role', role.id)
        await inter.response.send_message(get_str(inter.guild, 'M_SET_MUTE_ROLE_SET', role=role.mention),
                                          ephemeral=True)

        await role.edit(permissions=disnake.Permissions.none())
        await apply_mute_role_permissions(role)

    @commands.slash_command(name='unmute')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def unmute(
            self,
            inter: disnake.ApplicationCommandInteraction,
            member: disnake.Member,
    ):
        """
        Unmute a user {{CMD_UNMUTE}}

        Parameters
        ----------
        member: Member to unmute {{UNMUTE_MEMBER}}
        """

        if member == inter.author:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_SELF'))
        if member == self.bot.user:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ME'))
        if member.guild_permissions.administrator:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ADMINISTRATOR'))

        entry = PunishmentEntry.find(inter.guild, member, PunishmentType.Mute)
        if entry is None:
            raise EmbedableError(get_str(inter.guild, 'ERROR_UNMUTE_NOT_MUTED'))

        await entry.revoke()
        await inter.response.send_message(get_str(inter.guild, 'M_UNMUTE_UNMUTED', member=str(member)))

    @commands.slash_command(name='timeout')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def timeout(
            self,
            inter: disnake.ApplicationCommandInteraction,
            member: disnake.Member,
            duration: str,
            reason: str = None
    ):
        """
        Timeout a user on the server {{CMD_TIMEOUT}}

        Parameters
        ----------
        member: Member to timeout {{TIMEOUT_MEMBER}}
        duration: Duration (e.g. 1h30m) {{C_DURATION}}
        reason: Reason {{C_REASON}}
        """

        if member == inter.author:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_SELF'))
        if member == self.bot.user:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ME'))
        if member.guild_permissions.administrator:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ADMINISTRATOR'))

        duration_seconds = string_to_seconds(duration)
        if not 1 <= duration_seconds <= 2419200:
            raise EmbedableError(get_str(inter.guild, 'ERROR_TIMEOUT_INVALID_DURATION'))

        reason = reason or get_str(inter.guild, 'M_NO_REASON')

        entry = PunishmentEntry.find(inter.guild, member, PunishmentType.Timeout)
        if entry is None:
            entry = PunishmentEntry(inter.guild, member.id, PunishmentType.Timeout)

        entry.created_at = time.time()
        entry.duration = duration_seconds
        entry.reason = f"{inter.author}: {reason}"

        entry.save()
        await entry.execute()

        await inter.response.send_message(embed=generate_entry_embed(entry, inter.author, reason))

    @commands.slash_command(name='remove-timeout')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def remove_timeout(
            self,
            inter: disnake.ApplicationCommandInteraction,
            member: disnake.Member,
    ):
        """
        Remove timeout from a user {{CMD_REMOVE_TIMEOUT}}

        Parameters
        ----------
        member: Member to remove timeout from {{REMOVE_TIMEOUT_MEMBER}}
        """

        if member == inter.author:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_SELF'))
        if member == self.bot.user:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ME'))
        if member.guild_permissions.administrator:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ADMINISTRATOR'))

        entry = PunishmentEntry.find(inter.guild, member, PunishmentType.Timeout)
        if entry is None and member.current_timeout is None:
            raise EmbedableError(get_str(inter.guild, 'ERROR_REMOVE_TIMEOUT'))

        if entry is not None:
            await entry.revoke()
        else:
            await member.timeout(duration=0)

        await inter.response.send_message(get_str(inter.guild, 'M_REMOVE_TIMEOUT_REMOVED', member=str(member)))

    @commands.slash_command(name='punishment-entries')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def punishment_entries(
            self,
            inter: disnake.ApplicationCommandInteraction,
            punishment_type: str = commands.Param(choices=['all', 'mute', 'timeout', 'ban']),
            user: disnake.User = None,
            descending: bool = True
    ):
        """
        View all active punishment entries {{CMD_PUNISHMENT_ENTRIES}}

        Parameters
        ----------
        punishment_type: Punishment type {{PUNISHMENT_ENTRIES_TYPE}}
        user: Filter entries by this user (can be blank) {{PUNISHMENT_ENTRIES_USER}}
        descending: Show newest entries first {{PUNISHMENT_ENTRIES_DESCENDING}}
        """

        entries = []
        embeds = []
        user_id = user.id if user is not None else 0

        for _id, entry_data in punishment_entries.data.items():
            if entry_data.get('guild-id') != inter.guild.id:
                continue

            if punishment_type == entry_data.get('punishment-type') or punishment_type == 'all':
                if user_id == entry_data.get('user-id') or user is None:
                    entry = PunishmentEntry.get(_id)
                    entries.append(entry)

        entries = sorted(entries, key=lambda x: x.created_at, reverse=descending)
        if len(entries) == 0:
            embed = disnake.Embed(description=get_str(inter.guild, 'M_LIST_EMPTY'), color=Color.primary)
            return await inter.response.send_message(embed=embed, ephemeral=True)

        for i, entry in enumerate(entries, 1):
            embed = disnake.Embed(color=Color.primary)
            embed.title = get_str(inter.guild, 'T_PUNISHMENT_ENTRIES', current=i, total=len(entries))
            fields = {
                'F_USER': f"`{get_user_or_id(self.bot, entry.user_id)}`",
                "F_TYPE": f"`{get_str(inter.guild, 'F_' + entry.punishment_type.value.upper())}`",
                "F_CREATED_AT": f"<t:{int(entry.created_at)}:f>",
                "F_DURATION": '-' if entry.duration is None else f"`{seconds_to_string(entry.duration, inter.guild)}`",
                'F_REASON': f"`{entry.reason}`",
            }

            embed.description = '\n'.join(
                [f"**{get_str(inter.guild, name)}:** {value}" for name, value in fields.items()]
            )
            embeds.append(embed)

        paginator = Paginator(embeds=embeds, guild=inter.guild, timeout=600)
        await inter.response.send_message(embed=embeds[0], view=paginator, ephemeral=True)

    @commands.slash_command(name='punishment-tasks')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def punishment_tasks(
            self,
            inter: disnake.ApplicationCommandInteraction,
            punishment_type: str = commands.Param(choices=['all', 'ban']),
            descending: bool = True
    ):
        """
        View all punishment tasks {{CMD_PUNISHMENT_TASKS}}

        Parameters
        ----------
        punishment_type: Punishment type {{PUNISHMENT_TASKS_TYPE}}
        descending: Show newest entries first {{PUNISHMENT_TASKS_DESCENDING}}
        """

        tasks = []
        embeds = []

        for _id, task_data in punishment_tasks.data.items():
            if task_data.get('guild-id') != inter.guild.id:
                continue

            if punishment_type == task_data.get('punishment-type') or punishment_type == 'all':
                task = PunishmentTask.get(_id)
                tasks.append(task)

        tasks = sorted(tasks, key=lambda x: x.created_at, reverse=descending)
        if len(tasks) == 0:
            embed = disnake.Embed(description=get_str(inter.guild, 'M_LIST_EMPTY'), color=Color.primary)
            return await inter.response.send_message(embed=embed, ephemeral=True)

        for i, task in enumerate(tasks, 1):
            embed = disnake.Embed(color=Color.primary)
            embed.title = get_str(inter.guild, 'T_PUNISHMENT_TASKS', current=i, total=len(tasks))
            fields = {
                'F_USER': f"`{get_user_or_id(self.bot, task.user)}`",
                "F_TYPE": f"`{get_str(inter.guild, 'F_' + task.punishment_type.value.upper())}`",
                "F_CREATED_AT": f"<t:{int(task.created_at)}:f>",
                "F_DURATION": '-' if task.duration is None else f"`{seconds_to_string(task.duration, inter.guild)}`",
                'F_REASON': f"`{task.reason}`",
            }

            embed.description = '\n'.join(
                [f"**{get_str(inter.guild, name)}:** {value}" for name, value in fields.items()]
            )
            embeds.append(embed)

        paginator = Paginator(embeds=embeds, guild=inter.guild, timeout=600)
        await inter.response.send_message(embed=embeds[0], view=paginator, ephemeral=True)

    @commands.slash_command(name='ban')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def ban(
            self,
            inter: disnake.ApplicationCommandInteraction,
            member: disnake.Member = None,
            id_or_name: str = None,
            duration: str = None,
            reason: str = None
    ):
        """
        Ban a member from the server {{CMD_BAN}}

        Parameters
        ----------
        member: Member to ban {{BAN_MEMBER}}
        id_or_name: User ID or name (specify either user, their name or ID) {{C_ID_NAME}}
        duration: Duration (e.g. 1h30m) {{C_DURATION}}
        reason: Reason {{C_REASON}}
        """

        if member == inter.guild.owner or id_or_name in [inter.guild.owner.name, str(inter.guild.owner_id)]:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_OWNER'))
        if member == inter.author or id_or_name in [inter.author.name, str(inter.author.id)]:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_SELF'))
        if member == self.bot.user or id_or_name in [self.bot.user.name, str(self.bot.user.id)]:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ME'))
        if member is None and id_or_name is None:
            raise EmbedableError(get_str(inter.guild, 'M_ERROR_USER_NAME_OR_ID'))

        if duration is not None:
            duration = string_to_seconds(duration)
            if duration <= 0:
                duration = None

        reason = reason or get_str(inter.guild, 'M_NO_REASON')
        user = member or id_or_name

        _user = find_user(user)

        if _user is None:
            task = PunishmentTask.find(inter.guild, user, PunishmentType.Ban)
            if task is None:
                task = PunishmentTask(inter.guild, user, PunishmentType.Ban)

            task.created_at = time.time()
            task.duration = duration
            task.reason = f"{inter.author}: {reason}"
            task.save()

            return await inter.response.send_message(embed=generate_task_embed(task, inter.author, reason))

        entry = PunishmentEntry.find(inter.guild, _user, PunishmentType.Ban)
        if entry is None:
            entry = PunishmentEntry(inter.guild, _user.id, PunishmentType.Ban)

        entry.created_at = time.time()
        entry.duration = duration
        entry.reason = f"{inter.author}: {reason}"

        entry.save()
        await entry.execute()

        await inter.response.send_message(embed=generate_entry_embed(entry, inter.author, reason))

    @commands.slash_command(name='unban')
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def unban(
            self,
            inter: disnake.ApplicationCommandInteraction,
            user: disnake.User = None,
            id_or_name: str = None
    ):
        """
        Unban a user on the server {{CMD_UNBAN}}

        Parameters
        ----------
        user: User to unban {{UNBAN_USER}}
        id_or_name: User ID or name (specify either user, their name or ID) {{C_ID_NAME}}
        """

        if user == inter.guild.owner or id_or_name in [inter.guild.owner.name, str(inter.guild.owner_id)]:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_OWNER'))
        if user == inter.author or id_or_name in [inter.author.name, str(inter.author.id)]:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_SELF'))
        if user == self.bot.user or id_or_name in [self.bot.user.name, str(self.bot.user.id)]:
            raise EmbedableError(get_str(inter.guild, 'ERROR_COMMAND_ME'))
        if user is None and id_or_name is None:
            raise EmbedableError(get_str(inter.guild, 'M_ERROR_USER_NAME_OR_ID'))

        user = user or id_or_name
        _user = find_user(user)
        unbanned = False

        task = PunishmentTask.find(inter.guild, user, PunishmentType.Ban)
        if task is not None:
            task.revoke()
            unbanned = True

        if _user is not None:
            entry = PunishmentEntry.find(inter.guild, _user, PunishmentType.Ban)
            if entry is not None:
                await entry.revoke()
                unbanned = True

        if not unbanned:
            async for entry in inter.guild.bans():
                if entry.user == user or entry.user.name == user or str(entry.user.id) == user:
                    await inter.guild.unban(entry.user)
                    unbanned = True
                    user = entry.user
                    break

        if not unbanned:
            raise EmbedableError(get_str(inter.guild, 'ERROR_UNBAN_NOT_BANNED'))

        await inter.response.send_message(get_str(inter.guild, 'M_UNBAN_UNBANNED', user=user))


def setup(bot: commands.AutoShardedInteractionBot):
    bot.add_cog(ModerationCommands(bot))
