import asyncio
import codecs
import random

from discord import Guild, Embed
from discord import ApplicationContext, Option
from ..bot import DiscordBot, SlashCommand
from ..utils import convert_args


class Vegehint:
    def __init__(self, name, desc, num):
        self.name = name
        self.desc = desc
        self.id = num

    def to_embed(self):
        embed = Embed(title=self.name,
                              description=self.desc,
                              color=0x7bed24)
        embed.set_footer(text=f"Vegehint #{self.id}")
        return embed

    @classmethod
    def from_embed(cls, embed):
        embed_id = int(embed.footer.text[10:])
        return Vegehint(embed.title, embed.description, embed_id)


class Vegehints(SlashCommand, name="vegehint"):
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        super().__init__(bot, guild_ids)

        self.vegehints = []

        self.register(self.vegehint)

        if vege := self.bot.bot.get_guild(762888327161708615):
            asyncio.create_task(self.init_vegehints(vege))

    async def init_vegehints(self, vege: Guild):
        ch = vege.get_channel(836076080564535337)
        self.vegehints = list(map(lambda x: Vegehint.from_embed(x.embeds[0]),
                                  await ch.history().flatten()))

    def get_vegehint(self):
        return random.choice(self.vegehints)

    async def vegehint(
            self, ctx: ApplicationContext,
            flags: Option(str, "flags", required=False) = ""
    ):
        """Gets a random vegehint"""
        flags = convert_args(flags.split())

        if 'c' not in flags:
            try:
                hint = self.get_vegehint()
            except IndexError:
                await ctx.respond("No vegehints available at this time.",
                                  ephemeral=True)
            else:
                await ctx.respond(embed=hint.to_embed())

            return

        elif 812998213543133204 in [r.id for r in ctx.user.roles]:
            if 'n' in flags:
                name = flags['n'][0]
            else:
                await ctx.respond(
                    "Name not specified. Please use `-n <name>`.",
                    ephemeral=True)
                return

            if 'd' in flags:
                desc = flags['d'][0]
                desc = codecs.decode(desc, "unicode-escape")
            else:
                await ctx.respond("Description not specified. Please use "
                                  "`-d <description>`.", ephemeral=True)
                return

            embed = Embed(title=name, description=desc, color=0x7bed24)
            embed.set_footer(text=f"Vegehint #{len(self.vegehints) + 1}")

            self.vegehints.append(Vegehint.from_embed(embed))

            await ctx.channel.send(embed=embed)
            await ctx.respond("Done!", ephemeral=True)
