import disnake
from utils.language import get_str
from misc.colors import Color


class Paginator(disnake.ui.View):
    def __init__(self, embeds: list[disnake.Embed], guild: disnake.Guild, timeout: float = None):
        super().__init__(timeout=timeout)

        self.embeds = embeds
        self.index = 0
        self.guild = guild

        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"{get_str(self.guild, 'F_PAGINATOR_PAGE')} {i + 1}/{len(self.embeds)}")

        self.update_state()

    def update_state(self):
        self.first_page.disabled = self.prev_page.disabled = self.index == 0
        self.last_page.disabled = self.next_page.disabled = self.index == len(self.embeds) - 1

    @disnake.ui.button(label='<<', style=disnake.ButtonStyle.blurple)
    async def first_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.index = 0
        self.update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @disnake.ui.button(label='<', style=disnake.ButtonStyle.gray)
    async def prev_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.index -= 1
        self.update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @disnake.ui.button(label='>', style=disnake.ButtonStyle.gray)
    async def next_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.index += 1
        self.update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @disnake.ui.button(label='>>', style=disnake.ButtonStyle.blurple)
    async def last_page(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.index = len(self.embeds) - 1
        self.update_state()

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @staticmethod
    def generate_embeds(
            items: list,
            items_per_embed: int,
            empty_list_message: str,
            title: str = None,
            description: str = None,
            color: int = Color.primary
    ) -> list[disnake.Embed]:
        splitted_items = [items[i:i+items_per_embed] for i in range(0, len(items), items_per_embed)]
        embeds = []

        if len(items) == 0:
            embed = disnake.Embed(title=title, description=empty_list_message, color=color)
            return [embed]

        for chunk in splitted_items:
            embed = disnake.Embed(title=title, description=description or '', color=color)
            embed.description += '\n' * 2

            for item in chunk:
                if isinstance(item, tuple):
                    embed.add_field(name=item[0], value=item[1], inline=item[2])
                else:
                    embed.description += f"{item}\n"

            embeds.append(embed)

        return embeds
