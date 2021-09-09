import discord
import numpy as np
import psycopg2 as pg
from discord.ext import commands
from discord_slash import SlashContext
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option

from .utils import convert_args


class CoopSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.members = {}

    @cog_ext.cog_subcommand(guild_ids=[],
                            base="coop", name="add",
                            description="Adds a hero to your list of "
                                        "usable heroes.",
                            options=[
                                create_option("hero", "Name of the hero",
                                              str, True)
                            ])
    async def coop_add(self, ctx: SlashContext, hero: str):
        try:
            hero = self.bot.heromatcher.match(hero)
        except ValueError as e:
            await ctx.send(e.args[0], hidden=True)
            return

        await ctx.defer(hidden=True)

        try:
            self.bot.coop_db.execute(f"INSERT INTO heroes_owned "
                                     f"VALUES ({ctx.author_id}, {hero.id})")
        except pg.errors.UniqueViolation:
            await ctx.send(f"{hero.gamename} is already "
                           f"in your list of heroes!", hidden=True)
        else:
            await ctx.send(f"{hero.gamename} has been added "
                           f"to your list of heroes!", hidden=True)

    @cog_ext.cog_subcommand(guild_ids=[],
                            base="coop", name="remove",
                            description="Removes a hero from your list of "
                                        "usable heroes.",
                            options=[
                                create_option("hero", "Name of the hero",
                                              str, True)
                            ])
    async def coop_remove(self, ctx: SlashContext, hero: str):
        try:
            hero = self.bot.heromatcher.match(hero)
        except ValueError as e:
            await ctx.send(e.args[0], hidden=True)
            return

        await ctx.defer(hidden=True)

        if self.bot.coop_db.fetch(f"""
            SELECT FROM heroes_owned 
            WHERE id={ctx.author_id} AND hero={hero.id}
        """):
            self.bot.coop_db.execute(f"DELETE FROM heroes_owned "
                                     f"WHERE id={ctx.author_id} "
                                     f"AND hero={hero.id}")
            await ctx.send(f"Removed {hero.gamename} from "
                           "your list of heroes!", hidden=True)
        else:
            await ctx.send(f"{hero.gamename} is not in your list of "
                           f"heroes!", hidden=True)

    @cog_ext.cog_subcommand(guild_ids=[],
                            base="coop", name="list",
                            description="Lists your or someone else's heroes.",
                            options=[
                                create_option("user", "Whose heroes to view; "
                                                      "defaults to self",
                                              discord.Member, False)
                            ])
    async def coop_list(self, ctx: SlashContext,
                        user: discord.Member = None):
        if not ctx.channel.permissions_for(self.bot.bot).send_messages:
            await ctx.send("I do not have `Send Messages` permission "
                           "in this channel!")
        if not user:
            user = ctx.author

        await ctx.defer()

        heroes = self.bot.coop_db.fetch_flatten(f"""
            SELECT hero FROM heroes_owned WHERE id={user.id}
        """)

        # Converts to list of names
        heroes = map(lambda h: self.bot.heromatcher.get(h).emoji_id, heroes)
        heroes = map(lambda e: str(self.bot.bot.get_emoji(e)), heroes)

        # Convert to n x 7 array
        heroes = np.fromiter(heroes, "U64")
        heroes = np.pad(heroes, (0, -heroes.size % 7), constant_values='')
        heroes = heroes.reshape(-1, 7)

        hero_str = '\n'.join(map(lambda x: ''.join(x), heroes)) or "*None*"

        await ctx.send(f"__**{user.display_name}'s Heroes:**__")
        await ctx.channel.send(hero_str)

    @cog_ext.cog_subcommand(guild_ids=[],
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

        try:
            hero = self.bot.heromatcher.match(hero)
        except ValueError as e:
            await ctx.send(e.args[0], hidden=True)
            return

        await ctx.defer()

        discord_ids = self.bot.coop_db.fetch_flatten(f"""
            SELECT id FROM heroes_owned WHERE hero={hero.id}
        """)

        embed = discord.Embed(color=0x99ff24,
                              title=f"Users of {hero.gamename}")

        # do pings, otherwise member names
        members = map(lambda x: ctx.guild.get_member(x), discord_ids)
        members = [x for x in members if x]
        if 'n' not in args:
            members = map(lambda x: x.mention, members)
            embed.description = ', '.join(members)
        else:
            members = map(lambda x: x.display_name, members)
            embed.description = '\n'.join(members)

        await ctx.send(embed=embed)

# @commands.Cog.listener()
# async def on_message(self, msg: discord.Message):
#     if msg.channel.id == 808953170415058944:
#         if re.search(r"[A-Z0-9]{5}", msg.content):
#
#             if self._last_author != msg.author.id:
#                 if time.time() - self._last_time < 300:  # 5 min
#                     backup = self.bot.Vege.get_channel(835331220438646794)
#
#                     # If in archived then move
#                     if backup.category_id == 824288408355602442:
#                         cc = self.bot.Vege.get_channel(808953170415058944)
#                         await self.backup.enable(cc.position + 1)
#
#             self._last_author = msg.author.id
#             self._last_time = time.time()
