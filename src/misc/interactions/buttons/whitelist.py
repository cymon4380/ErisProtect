import disnake
from utils.language import get_str
from misc.colors import Color
from models.whitelist import AntiNukePermission, AntiNukePermissions


class WhitelistAdd(disnake.ui.View):
    def __init__(self, user: disnake.User, guild: disnake.Guild, timeout: float = None):
        super().__init__(timeout=timeout)

        self.user = user
        self.guild = guild
        self.permissions = AntiNukePermissions.from_database(user.id, guild)

        available_perms = list(AntiNukePermission)

        for permission in available_perms:
            if self.permissions.has_permissions(permission):
                button_style = disnake.ButtonStyle.green
            else:
                button_style = disnake.ButtonStyle.red

            self.add_item(
                disnake.ui.Button(
                    style=button_style,
                    label=AntiNukePermissions.get_display_name(self.guild, permission),
                    custom_id=permission.value,
                )
            )

        self.add_item(
            disnake.ui.Button(
                label=get_str(self.guild, 'A_SAVE'),
                style=disnake.ButtonStyle.blurple,
                custom_id=f"wl_save,{self.user.id}"
            )
        )

        self.add_item(
            disnake.ui.Button(
                label=get_str(self.guild, 'A_CANCEL'),
                style=disnake.ButtonStyle.gray,
                custom_id='wl_cancel'
            )
        )
