import discord
import re
import time
import yaml
from discord.ext import commands
from discord_slash import SlashContext
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option

from .utils import HeroMatcher, BackupChannel, convert_args


class CoopSlash(commands.Cog):
    discord_ids = [762888327161708615, 754534986077569215]
    def __init__(self, bot):
        self.bot = bot

        self.members = {}

        self._last_author = None
        self._last_time = 0

        _backup = self.bot.Vege.get_channel(835331220438646794)

        everyone = self.bot.Vege.default_role
        mbot = self.bot.Vege.get_role(849489655132717107)
        admin = self.bot.Vege.get_role(812998213543133204)
        overwrites = {
            everyone: discord.PermissionOverwrite(
                read_messages=True
            ),
            mbot: discord.PermissionOverwrite(
                read_messages=True
            ),
            admin: discord.PermissionOverwrite(
                manage_permissions=False
            )
        }
        self.backup = BackupChannel(_backup, 900, overwrites,
                                    category_id=762888327808417793)

    @cog_ext.cog_subcommand(guild_ids=discord_ids,
                            base="coop", name="add",
                            description="Adds a hero to your list of "
                                        "usable heroes.",
                            options=[
                                create_option("hero", "Name of the hero",
                                              str, True)
                            ])
    async def coop_add(self, ctx: SlashContext, hero: str):
        try:
            hero = HeroMatcher.match(hero)
        except ValueError as e:
            await ctx.send(e.args[0], hidden=True)
            return

        with open("coop.yml") as f:
            data = yaml.safe_load(f) or {}

        if ctx.author_id not in data:
            data[ctx.author_id] = []

        if hero.gamename not in data[ctx.author_id]:
            data[ctx.author_id].append(hero.gamename)
        else:
            await ctx.send(f"{hero.gamename} is already in your list of "
                           f"heroes!", hidden=True)
            return

        with open("coop.yml", 'w') as f:
            yaml.safe_dump(data, f)

        await ctx.send(f"Added {hero.gamename} to your list of heroes!",
                       hidden=True)

    @cog_ext.cog_subcommand(guild_ids=discord_ids,
                            base="coop", name="remove",
                            description="Removes a hero from your list of "
                                        "usable heroes.",
                            options=[
                                create_option("hero", "Name of the hero",
                                              str, True)
                            ])
    async def coop_remove(self, ctx: SlashContext, hero: str):
        try:
            hero = HeroMatcher.match(hero)
        except ValueError as e:
            await ctx.send(e.args[0], hidden=True)
            return

        with open("coop.yml") as f:
            data = yaml.safe_load(f) or {}

        if ctx.author_id not in data:
            data[ctx.author_id] = []

        if hero.gamename in data[ctx.author_id]:
            data[ctx.author_id].remove(hero.gamename)
        else:
            await ctx.send(f"{hero.gamename} is not in your list of "
                           f"heroes!", hidden=True)
            return

        with open("coop.yml", 'w') as f:
            yaml.safe_dump(data, f)

        await ctx.send(f"Removed {hero.gamename} from your list of heroes!",
                       hidden=True)

    @cog_ext.cog_subcommand(guild_ids=discord_ids,
                            base="coop", name="list",
                            description="Lists your or someone else's heroes.",
                            options=[
                                create_option("user", "Whose heroes to view; "
                                                      "defaults to self",
                                              discord.Member, False)
                            ])
    async def coop_list(self, ctx: SlashContext,
                        user: discord.Member = None):
        with open("coop.yml") as f:
            data = yaml.safe_load(f) or {}

        if user is None:
            user = ctx.author

        if user.id not in data:
            await ctx.send(f"{user.display_name} has not registered "
                           f"any of their heroes!")
            return

        embed = discord.Embed(color=0x00ffd9)
        embed.set_author(name=f"{user.display_name}'s Heroes",
                         icon_url=user.avatar_url)
        embed.description = '\n'.join(data[user.id])

        await ctx.send(embed=embed)

    @cog_ext.cog_subcommand(guild_ids=discord_ids,
                            base="coop", name="find",
                            description="Searches for people "
                                        "with a specific hero.",
                            options=[
                                create_option("hero", "Name of the hero",
                                              str, True),
                                create_option("flags", "n: names only",
                                              str, False)
                            ])
    async def coop_find(self, ctx: SlashContext, hero: str, flags: str = ''):
        args = convert_args(flags.split())
        print(args)

        try:
            hero = HeroMatcher.match(hero)
        except ValueError as e:
            await ctx.send(e.args[0], hidden=True)
            return

        with open("coop.yml") as f:
            data = yaml.safe_load(f) or {}

        people = []

        for k, v in data.items():
            if hero.gamename in v:
                people.append(k)

        embed = discord.Embed(color=0x99ff24,
                              title=f"Users of {hero.gamename}")
        if 'n' not in args:
            members = map(lambda x: f"<@{x}>", people)
            embed.description = ','.join(members)
        else:
            members = map(lambda x: self.bot.Vege.get_member(x).display_name,
                          people)
            embed.description = '\n'.join(members)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.channel.id == 808953170415058944:
            if re.search(r"[A-Z0-9]{5}", msg.content):

                if self._last_author != msg.author.id:
                    if time.time() - self._last_time < 300:  # 5 min
                        backup = self.bot.Vege.get_channel(835331220438646794)

                        # If in archived then move
                        if backup.category_id == 824288408355602442:
                            cc = self.bot.Vege.get_channel(808953170415058944)
                            await self.backup.enable(cc.position + 1)

                self._last_author = msg.author.id
                self._last_time = time.time()
