import discord
import codecs
import random
from discord.ext import commands
from discord_slash import ApplicationContext
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option

from .utils import convert_args


class Vegehint:
    def __init__(self, name, desc, num):
        self.name = name
        self.desc = desc
        self.id = num

    def to_embed(self):
        embed = discord.Embed(title=self.name,
                              description=self.desc,
                              color=0x7bed24)
        embed.set_footer(text=f"Vegehint #{self.id}")
        return embed

    @classmethod
    def from_embed(cls, embed):
        embed_id = int(embed.footer.text[10:])
        return Vegehint(embed.title, embed.description, embed_id)


class Vegehints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.vegehints = []

    async def init_vegehints(self):
        ch = self.bot.Vege.get_channel(836076080564535337)
        self.vegehints = list(map(lambda x: Vegehint.from_embed(x.embeds[0]),
                                  await ch.history().flatten()))

    def get_vegehint(self):
        return random.choice(self.vegehints)

    @cog_ext.cog_slash(guild_ids=[762888327161708615],
                       name="vegehint",
                       description="Gets a random vegehint!",
                       options=[
                           create_option("flags", "Optional flags", str, False)
                       ])
    async def vegehint(self, ctx: ApplicationContext, flags: str = ""):
        flags = convert_args(flags.split())

        if 'c' not in flags:
            try:
                hint = self.get_vegehint()
            except IndexError:
                await ctx.send("No vegehints available at this time.",
                               hidden=True)
            else:
                await ctx.send(embed=hint.to_embed())

            return

        elif 812998213543133204 in [r.id for r in ctx.author.roles]:
            if 'n' in flags:
                name = flags['n'][0]
            else:
                await ctx.send("Name not specified. Please use `-n <name>`.",
                               hidden=True)
                return

            if 'd' in flags:
                desc = flags['d'][0]
                desc = codecs.decode(desc, "unicode-escape")
            else:
                await ctx.send("Description not specified. Please use "
                               "`-d <description>`.", hidden=True)
                return

            embed = discord.Embed(title=name, description=desc, color=0x7bed24)
            embed.set_footer(text=f"Vegehint #{len(self.vegehints) + 1}")

            self.vegehints.append(Vegehint.from_embed(embed))

            await ctx.channel.send(embed=embed)
            await ctx.send("Done!", hidden=True)
