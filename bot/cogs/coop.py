import discord
import psycopg2 as pg
from discord.ext import commands
from discord_slash import SlashContext
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option

from .utils import HeroMatcher, DatabaseConnection, convert_args


class CoopSlash(commands.Cog):
    discord_ids = DatabaseConnection.fetch_flatten(f"""
        SELECT guild_id FROM slash_guilds 
        INNER JOIN slashes ON slash_guilds.slash_id = slashes.id 
        AND slashes.name = 'coop'
    """)

    def __init__(self, bot):
        self.bot = bot

        self.members = {}

        self._last_author = None
        self._last_time = 0

        # _backup = self.bot.Vege.get_channel(835331220438646794)
        #
        # everyone = self.bot.Vege.default_role
        # mbot = self.bot.Vege.get_role(849489655132717107)
        # admin = self.bot.Vege.get_role(812998213543133204)
        # overwrites = {
        #     everyone: discord.PermissionOverwrite(
        #         read_messages=True
        #     ),
        #     mbot: discord.PermissionOverwrite(
        #         read_messages=True
        #     ),
        #     admin: discord.PermissionOverwrite(
        #         manage_permissions=False
        #     )
        # }
        # self.backup = BackupChannel(_backup, 900, overwrites,
        #                             category_id=762888327808417793)

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

        await ctx.defer(hidden=True)

        try:
            DatabaseConnection.execute(f"INSERT INTO heroes_owned "
                                       f"VALUES ({ctx.author_id}, {hero.id})")
        except pg.errors.UniqueViolation:
            await ctx.send(f"{hero.gamename} is already "
                           f"in your list of heroes!", hidden=True)
        else:
            await ctx.send(f"{hero.gamename} has been added "
                           f"to your list of heroes!", hidden=True)

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

        await ctx.defer(hidden=True)

        if DatabaseConnection.fetch(f"""
            SELECT FROM heroes_owned 
            WHERE id={ctx.author_id} AND hero={hero.id}
        """):
            DatabaseConnection.execute(f"REMOVE FROM heroes_owned"
                                       f"WHERE id={ctx.author_id} "
                                       f"AND hero={hero.id}")
            await ctx.send(f"Removed {hero.gamename} from "
                           "your list of heroes!", hidden=True)
        else:
            await ctx.send(f"{hero.gamename} is not in your list of "
                           f"heroes!", hidden=True)

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
        if not user:
            user = ctx.author

        await ctx.defer()

        heroes = DatabaseConnection.fetch_flatten(f"""
            SELECT hero FROM heroes_owned WHERE id={user.id}
        """)

        # Converts to list of names
        heroes = map(lambda h: HeroMatcher.get(h).gamename, heroes)
        hero_str = '\n'.join(heroes) or "*None*"

        embed = discord.Embed(colour=0x00ffd9, description=hero_str)
        embed.set_author(name=f"{user.display_name}'s Heroes",
                         icon_url=user.avatar_url)

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

        try:
            hero = HeroMatcher.match(hero)
        except ValueError as e:
            await ctx.send(e.args[0], hidden=True)
            return

        await ctx.defer()

        discord_ids = DatabaseConnection.fetch_flatten(f"""
            SELECT id FROM heroes_owned WHERE hero={hero.id}
        """)

        embed = discord.Embed(color=0x99ff24,
                              title=f"Users of {hero.gamename}")

        # do pings, otherwise member names
        if 'n' not in args:
            members = map(lambda x: f"<@{x}>", discord_ids)
            embed.description = ', '.join(members)
        else:
            members = map(lambda x: ctx.guild.get_member(x).display_name,
                          discord_ids)
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
