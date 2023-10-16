import os
import disnake
import json
from utils.language import get_str
from misc.collections import config
from utils.messages import get_notification_embed, NotificationType


class LanguageSelectMenu(disnake.ui.StringSelect):
    def __init__(self):
        available_langs = []
        self.lang_codes = {}
        lang_packs_dir = os.path.join(os.getcwd(), 'lang_packs', 'misc')

        for f in os.listdir(lang_packs_dir):
            file_path = os.path.join(lang_packs_dir, f)

            if not f.endswith('.json'):
                continue
            if not os.path.isfile(file_path):
                continue

            with open(file_path, 'r', encoding='utf-8') as file:
                lang_pack_file = json.load(file)

            try:
                localized_by = lang_pack_file['L_LOCALIZED_BY']
                available_langs.append(disnake.SelectOption(
                    label=lang_pack_file['L_NAME'],
                    description=f"{lang_pack_file['M_LANGUAGE_LOCALIZED_BY']}: {', '.join(localized_by)}"
                ))
                self.lang_codes[lang_pack_file['L_NAME']] = f.split('.')[0]
            except KeyError:
                pass

        super().__init__(options=available_langs)

    async def callback(self, inter: disnake.MessageInteraction):
        config.set_value(inter.guild.id, 'language', self.lang_codes.get(self.values[0]))

        embed = get_notification_embed(
            guild=inter.guild,
            notification_type=NotificationType.EmbedDone,
            message=f'{get_str(inter.guild, "M_LANGUAGE_SET")} `{self.values[0]}`.'
        )

        await inter.response.edit_message(embed=embed, components=[])


class LanguageSelectView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(LanguageSelectMenu())
