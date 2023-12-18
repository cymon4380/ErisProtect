import disnake
from disnake.ext import commands
from misc.colors import Color
from misc.interactions.buttons.paginator import Paginator
from misc.interactions.buttons.whitelist import WhitelistAdd
from utils.language import get_str
from misc.collections import whitelist
from models.whitelist import AntiNukePermission, AntiNukePermissions
from utils.string_format import get_user_or_id
from utils.messages import send_notification, get_notification_embed, NotificationType
from models.bot import EmbedableError


class WhitelistCommands(commands.Cog):
    def __init__(self, bot: commands.AutoShardedInteractionBot):
        self.bot = bot

    @commands.slash_command(name='whitelist')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def whitelist(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @whitelist.sub_command(name='list')
    async def whitelist_list(self, inter: disnake.ApplicationCommandInteraction):
        """
        List of whitelisted users {{CMD_WHITELIST_LIST}}
        """

        display_items = []
        for _id, permissions in whitelist.get_document(inter.guild.id, default={}).items():
            if _id == '_id':
                continue

            user_id = int(_id)
            perms = AntiNukePermissions(user_id, inter.guild, permissions)
            display_user = get_user_or_id(self.bot, user_id)

            display_items.append(f"`{display_user}`: {perms.count_permissions()}/{len(perms.permissions)}")

        embeds = Paginator.generate_embeds(
            items=display_items,
            items_per_embed=20,
            empty_list_message=get_str(inter.guild, 'M_LIST_EMPTY'),
            title=get_str(inter.guild, 'C_WHITELIST_TITLE'),
            description=f"{get_str(inter.guild, 'M_WHITELIST_DESC')} `/whitelist info`",
        )

        await inter.response.send_message(embed=embeds[0], view=Paginator(embeds, inter.guild), ephemeral=True)

    @whitelist.sub_command(name='info')
    async def whitelist_info(
            self,
            inter: disnake.ApplicationCommandInteraction,
            user: disnake.User = None,
            user_id: str = None
    ):
        """
        Get more info about whitelisted user {{CMD_WHITELIST_INFO}}

        Parameters
        ----------
        user: Whitelisted user {{WHITELIST_INFO_USER}}
        user_id: ID of whitelisted user {{WHITELIST_INFO_USER_ID}}
        """

        if user is None and user_id is None:
            raise EmbedableError(get_str(inter.guild, 'M_ERROR_USER_OR_ID'))

        if user_id is not None:
            if not user_id.isdigit():
                raise EmbedableError(get_str(inter.guild, 'M_ERROR_INVALID_ID'))

        uid = user.id if user is not None else int(user_id)

        anti_nuke_perms = AntiNukePermissions.from_database(uid, inter.guild)

        embed = disnake.Embed(
            title=get_str(inter.guild, 'C_WHITELIST_INFO_TITLE'),
            color=Color.primary
        )

        embed.add_field(
            name=get_str(inter.guild, 'F_USER'),
            value=f"`{get_user_or_id(self.bot, uid)}`",
            inline=False
        )

        display_perms = []
        for perm in AntiNukePermission:
            display_name = AntiNukePermissions.get_display_name(inter.guild, perm)
            emoji = '✅' if anti_nuke_perms.has_permissions(perm) else '❌'

            display_perms.append(f"`{display_name}`: {emoji}")

        embed.add_field(
            name=get_str(inter.guild, 'F_PERMISSIONS'),
            value='\n'.join(display_perms),
            inline=False
        )

        await inter.response.send_message(embed=embed, ephemeral=True)

    @whitelist.sub_command(name='add')
    async def whitelist_add(
            self,
            inter: disnake.ApplicationCommandInteraction,
            user: disnake.User
    ):
        """
        Add/edit a user to the whitelist {{CMD_WHITELIST_ADD}}

        Parameters
        ----------
        user: User to edit their permissions {{WHITELIST_ADD_USER}}
        """

        if inter.author.id != inter.guild.owner_id:
            raise EmbedableError(get_str(inter.guild, 'M_ERROR_NOT_SERVER_OWNER'))
        if user.id == inter.author.id:
            raise EmbedableError(get_str(inter.guild, 'ERROR_WHITELIST_ADD_SELF'))
        if user == self.bot.user:
            raise EmbedableError(get_str(inter.guild, 'ERROR_WHITELIST_ADD_ME'))

        await inter.response.send_message(
            f"## {get_str(inter.guild, 'M_WHITELIST_ADD_CHOOSE_PERMS')} `{user}`.",
            view=WhitelistAdd(user, inter.guild),
            ephemeral=True
        )

    @whitelist.sub_command(name='grant-all')
    async def whitelist_grant_all(
            self,
            inter: disnake.ApplicationCommandInteraction,
            user: disnake.User
    ):
        """
        Grant all permissions to a user (DANGEROUS) {{CMD_WHITELIST_GRANT_ALL}}

        Parameters
        ----------
        user: User to grant all permissions {{WHITELIST_GRANT_ALL_USER}}
        """

        if inter.author.id != inter.guild.owner_id:
            raise EmbedableError(get_str(inter.guild, 'M_ERROR_NOT_SERVER_OWNER'))
        if user.id == inter.author.id:
            raise EmbedableError(get_str(inter.guild, 'ERROR_WHITELIST_ADD_SELF'))
        if user == self.bot.user:
            raise EmbedableError(get_str(inter.guild, 'ERROR_WHITELIST_ADD_ME'))

        perms = AntiNukePermissions(user.id, inter.guild)
        perms.grant_all()

        await send_notification(
            inter,
            NotificationType.EmbedDone,
            f"{get_str(inter.guild, 'M_WHITELIST_GRANT_ALL')} `{user}`."
        )

    @whitelist.sub_command(name='remove')
    async def whitelist_remove(
            self,
            inter: disnake.ApplicationCommandInteraction,
            user: disnake.User = None,
            user_id: str = None
    ):
        """
        Remove a user from the whitelist {{CMD_WHITELIST_REMOVE}}

        Parameters
        ----------
        user: User to remove {{WHITELIST_REMOVE_USER}}
        user_id: User ID to remove {{WHITELIST_REMOVE_USER_ID}}
        """

        if user is None and user_id is None:
            raise EmbedableError(get_str(inter.guild, 'M_ERROR_USER_OR_ID'))
        if inter.author.id != inter.guild.owner_id:
            raise EmbedableError(get_str(inter.guild, 'M_ERROR_NOT_SERVER_OWNER'))
        if user_id is not None:
            if not user_id.isdigit():
                raise EmbedableError(get_str(inter.guild, 'M_ERROR_INVALID_ID'))

        uid = user.id if user is not None else int(user_id)

        if uid == inter.author.id:
            raise EmbedableError(get_str(inter.guild, 'ERROR_WHITELIST_REMOVE_SELF'))
        if uid == self.bot.user.id:
            raise EmbedableError(get_str(inter.guild, 'ERROR_WHITELIST_REMOVE_ME'))

        perms = AntiNukePermissions.from_database(uid, inter.guild)

        if perms.count_permissions() == 0:
            raise EmbedableError(
                f"`{get_user_or_id(self.bot, uid)}` {get_str(inter.guild, 'ERROR_WHITELIST_REMOVE_NOT_EXISTS')}"
            )

        perms.clear()

        await send_notification(
            inter,
            NotificationType.EmbedDone,
            f"`{get_user_or_id(self.bot, uid)}` {get_str(inter.guild, 'M_WHITELIST_REMOVE')}"
        )

    @commands.Cog.listener('on_button_click')
    async def on_button_click(self, inter: disnake.MessageInteraction):
        view = disnake.ui.View.from_message(inter.message)

        if view is None:
            return

        for item in view.children:
            if not isinstance(item, disnake.ui.Button):
                continue

            if item.custom_id != inter.component.custom_id:
                continue

            if item.custom_id in [v.value for v in AntiNukePermission]:
                enabled = item.style == disnake.ButtonStyle.green

                item.style = disnake.ButtonStyle.red if enabled else disnake.ButtonStyle.green
                return await inter.response.edit_message(view=view)

            if inter.component.custom_id.startswith('wl_save'):
                user_id = int(inter.component.custom_id.split(',')[1])
                display_user = get_user_or_id(self.bot, user_id)

                perms = AntiNukePermissions.from_database(user_id, inter.guild)

                for _item in view.children:
                    if not isinstance(_item, disnake.ui.Button):
                        continue

                    if _item.custom_id in [v.value for v in AntiNukePermission]:
                        perms.permissions[_item.custom_id] = _item.style == disnake.ButtonStyle.green

                perms.save()

                if perms.count_permissions() > 0:
                    embed_msg = f"{get_str(inter.guild, 'M_WHITELIST_ADD_GRANTED')} `{display_user}`:\n"
                    for perm in AntiNukePermission:
                        if not perms.has_permissions(perm):
                            continue
                        embed_msg += f"> `{get_str(inter.guild, 'F_PERM_' + perm.value.upper())}`\n"
                else:
                    embed_msg = f"`{display_user}` {get_str(inter.guild, 'M_WHITELIST_REMOVE')}"

                embed = get_notification_embed(
                    inter.guild,
                    NotificationType.EmbedDone,
                    embed_msg
                )

                return await inter.response.edit_message(embed=embed, content=None, view=None)

            if inter.component.custom_id == 'wl_cancel':
                return await inter.response.edit_message(
                    content=f"## {get_str(inter.guild, 'M_CANCELED')}",
                    view=None
                )


def setup(bot):
    bot.add_cog(WhitelistCommands(bot))
