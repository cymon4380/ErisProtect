import disnake
from utils.language import get_str
from utils.messages import get_notification_embed, NotificationType
from models.whitelist import AntiNukePermission, AntiNukePermissions
from models.nuke_score import NukeScoreEntry, NukeThreshold
from misc.colors import Color
from models.bot import EmbedableError
from misc.collections import nuke_scores


class ValueChangeMenu(disnake.ui.StringSelect):
    def __init__(self, guild: disnake.Guild):
        self.guild = guild

        options = []
        for permission in AntiNukePermission:
            display_name = AntiNukePermissions.get_display_name(self.guild, permission)

            options.append(
                disnake.SelectOption(
                    label=display_name,
                    description=f"{get_str(self.guild, 'M_NUKE_SCORE_DROPDOWN_DESCRIPTION')}: {display_name}",
                )
            )

        super().__init__(options=options, placeholder=get_str(self.guild, 'M_NUKE_SCORE_CHANGE_VALUES'))

    async def callback(self, inter: disnake.MessageInteraction):
        permission = AntiNukePermissions.get_permission_by_display_name(self.guild, self.values[0])

        if permission is None:
            return

        await inter.response.send_modal(ChangeValueModal(self.guild, permission))


class ValueChangeView(disnake.ui.View):
    def __init__(self, guild: disnake.Guild):
        self.guild = guild

        super().__init__(timeout=None)
        self.add_item(ValueChangeMenu(guild))

        set_threshold_btn = disnake.ui.Button(
            label=get_str(self.guild, 'M_NUKE_SCORE_SET_THRESHOLD'),
            style=disnake.ButtonStyle.blurple,
            custom_id='set_nuke_score_threshold'
        )

        self.add_item(set_threshold_btn)

    @staticmethod
    def get_embed(guild: disnake.Guild) -> disnake.Embed:
        embed = disnake.Embed(color=Color.primary, title=get_str(guild, 'C_NUKE_SCORE_TITLE'))
        permissions = []

        for permission in AntiNukePermission:
            entry = NukeScoreEntry.from_database(permission, guild)

            permissions.append(
                f"`{AntiNukePermissions.get_display_name(guild, permission)}`: "
                + f"{entry.value} / {entry.cooldown} {get_str(guild, 'S')}"
            )

        embed.description = '\n'.join(permissions)
        embed.description += f"\n\n`{get_str(guild, 'M_NUKE_SCORE_THRESHOLD')}`: {NukeThreshold.get(guild)}"

        return embed


class ChangeValueModal(disnake.ui.Modal):
    def __init__(self, guild: disnake.Guild, permission: AntiNukePermission):
        self.guild = guild
        self.permission = permission

        components = [
            disnake.ui.TextInput(
                label=get_str(self.guild, 'M_NUKE_SCORE_VALUE'),
                custom_id='value',
                max_length=4,
                required=False
            ),
            disnake.ui.TextInput(
                label=get_str(self.guild, 'M_NUKE_SCORE_COOLDOWN'),
                custom_id='cooldown',
                max_length=4,
                required=False
            )
        ]

        super().__init__(
            title=AntiNukePermissions.get_display_name(self.guild, self.permission),
            components=components
        )

    async def callback(self, inter: disnake.ModalInteraction):
        value = inter.text_values.get('value')
        cooldown = inter.text_values.get('cooldown')

        entry = NukeScoreEntry.from_database(self.permission, self.guild)

        if len(value) > 0:
            if value.isdigit():
                entry.value = int(value)

        if len(cooldown) > 0:
            if cooldown.isdigit():
                entry.cooldown = int(cooldown)

        entry.save()
        await inter.response.edit_message(embed=ValueChangeView.get_embed(self.guild))


class SetThresholdModal(disnake.ui.Modal):
    def __init__(self, guild: disnake.Guild):
        self.guild = guild

        components = [
            disnake.ui.TextInput(
                label=get_str(self.guild, 'M_NUKE_SCORE_THRESHOLD'),
                custom_id='value',
                max_length=4,
                required=True
            )
        ]

        super().__init__(
            title=get_str(self.guild, 'M_NUKE_SCORE_SET_THRESHOLD'),
            components=components
        )

    async def callback(self, inter: disnake.ModalInteraction):
        value = inter.text_values.get('value')

        if len(value) > 0:
            if value.isdigit():
                nuke_scores.set_value(self.guild.id, 'threshold', int(value))

        await inter.response.edit_message(embed=ValueChangeView.get_embed(self.guild))
