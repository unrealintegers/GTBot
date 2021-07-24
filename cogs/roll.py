from random import randint, sample

import discord
from discord.ext import commands


class RollCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def roll(self, ctx, *args):
        stats = {"Def": (153.8, 172.2),
                 "Damage Reduction": (62, 62)}
        opts = {
            "Skill Damage": (4, 12, 1),
            "Weapon Skill Regen Speed": (3, 8, 1),
            "Def": (3, 8, 1),
            "HP": (3, 7, 1)
        }
        subs = {
            "Light Atk": (5, 15, 1),
            "Dark Atk": (5, 15, 1),
            "Basic Atk": (5, 15, 1),
            "Fire Atk": (5, 15, 1),
            "Earth Atk": (5, 15, 1),
            "Water Atk": (5, 15, 1)
        }
        picked_subs = []
        max_subs = 1

        desc = ""

        for stat in stats:
            ran = stats[stat][1] - stats[stat][0]
            percent = randint(0, 10) * 0.1
            desc += f"**{stat}** {round(percent * ran + stats[stat][0], 1):g} " \
                    f"*({100 * percent:.1f}%)*\n"
        desc += "\n"
        for opt in opts:
            ran = opts[opt][1] - opts[opt][0]
            steps = ran / opts[opt][2]
            percent = randint(0, steps) / steps
            desc += f"**{opt}** +{round(percent * ran + opts[opt][0], 1):g}% " \
                    f"*({100 * percent:.1f}%)*\n"
        desc += "\n"
        for sub in subs:
            if randint(0, 1):
                picked_subs.append(sub)
        picked_subs = sample(picked_subs, min(len(picked_subs), max_subs))
        for sub in picked_subs:
            ran = subs[sub][1] - subs[sub][0]
            steps = ran / subs[sub][2]
            percent = randint(0, steps) / steps
            desc += f"**{sub}** +{round(percent * ran + subs[sub][0], 1):g}% " \
                    f"*({100 * percent:.1f}%)*\n"

        embed = discord.Embed(title="Captain's Mirror Shield", color=0xaada20,
                              description=desc)

        await ctx.send(embed=embed)
