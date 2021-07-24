import math

import discord
from discord.ext import commands
from fuzzywuzzy import process, fuzz

from .checks import *


def match_member(name, score=85):
    with open("members.txt") as f:
        members = f.read().split('\n')

    top = process.extract(name, members, scorer=fuzz.partial_ratio)
    return list(filter(lambda x: x[1] >= score, top))


class MemberCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="addmember")
    @commands.is_owner()
    async def add_member(self, ctx, *, name):
        if ' ' in name or '\n' in name:
            await ctx.send("Name cannot contain spaces or line breaks!")
            return

        with open("members.txt") as f:
            members = f.read().split('\n')

        if name in members:
            await ctx.send("Player already in member list!")
            return

        members.append(name)
        members.sort(key=lambda n: n.lower())

        with open("members.txt", "w") as f:
            f.write('\n'.join(members))
        await ctx.send("Done!")

    @commands.command(name="removemember")
    @commands.is_owner()
    async def removemember(self, ctx, *, name):
        with open("members.txt") as f:
            members = f.read().split('\n')

        names = match_member(name)
        if not names:
            await ctx.send("Member not found!")
            return

        if len(names) > 1:
            await ctx.send("Do something!")
            return

        assert names[0][0] in members  # How??
        members.remove(names[0][0])
        with open("members.txt", "w", newline="") as f:
            f.write('\n'.join(members))

        await ctx.send(f"Removed {names[0][0]} from the list!")

    @commands.command()
    @commands.check(check_category(806834564575002624))
    async def list(self, ctx):
        with open("members.txt") as f:
            members = f.read().split('\n')

        if len(members) > 1990:
            await ctx.send("Why is this so long??")
            return

        embed = discord.Embed(title="Vegemites Member List",
                              colour=0xf57316)

        size = math.ceil(len(members) / 3)
        left = members[: size]
        mid = members[size: size * 2]
        right = members[size * 2:]
        embed.add_field(name="\u200b", value='\n'.join(left))
        embed.add_field(name="\u200b" * 2, value='\n'.join(mid))
        embed.add_field(name="\u200b" * 3, value='\n'.join(right))

        await ctx.send(embed=embed)
