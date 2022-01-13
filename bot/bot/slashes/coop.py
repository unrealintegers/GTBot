from typing import List

import numpy as np
import psycopg2 as pg
from discord import ApplicationContext, Option
from discord import Member, Embed

from ..bot import DiscordBot, SlashCommand


class Coop(SlashCommand):
    def __init__(self, bot: DiscordBot, guild_ids: List[int]):
        super().__init__(bot, guild_ids)

        self.coop = bot.bot.create_group(
            "coop", "No Description", guild_ids=self.guild_ids
        )

        self.coop.command()(self.add)
        self.coop.command()(self.remove)
        self.coop.command()(self.list)
        self.coop.command()(self.find)

    async def add(
            self, ctx: ApplicationContext,
            hero: Option(str, "hero to add")
    ):
        """Adds a hero to your list of usable heroes"""
        try:
            hero = self.bot.heromatcher.match(hero)
        except ValueError as e:
            await ctx.respond(e.args[0], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        try:
            self.bot.coop_db.execute(f"INSERT INTO heroes_owned "
                                     f"VALUES ({ctx.user.id}, {hero.id})")
        except pg.errors.UniqueViolation:  # noqa
            await ctx.respond(f"{hero.gamename} is already "
                              f"in your list of heroes!", ephemeral=True)
        else:
            await ctx.respond(f"{hero.gamename} has been added "
                              f"to your list of heroes!", ephemeral=True)

    async def remove(
            self, ctx: ApplicationContext,
            hero: Option(str, "hero to remove")
    ):
        """Removes a hero from your list of heroes"""
        try:
            hero = self.bot.heromatcher.match(hero)
        except ValueError as e:
            await ctx.respond(e.args[0], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        if self.bot.coop_db.fetch(f"""
            SELECT FROM heroes_owned
            WHERE id={ctx.user.id} AND hero={hero.id}
        """):
            self.bot.coop_db.execute(f"DELETE FROM heroes_owned "
                                     f"WHERE id={ctx.user.id} "
                                     f"AND hero={hero.id}")
            await ctx.respond(f"Removed {hero.gamename} from "
                              "your list of heroes!", ephemeral=True)
        else:
            await ctx.respond(f"{hero.gamename} is not in your list of "
                              f"heroes!", ephemeral=True)

    async def list(
            self, ctx: ApplicationContext,
            user: Option(Member, "whose heroes to list, default self",
                         required=False)
    ):
        """Lists your or someone else's heroes"""
        perm = ctx.channel.permissions_for(ctx.guild.me)
        if not perm.administrator and not perm.send_messages:
            await ctx.respond("I do not have `Send Messages` permission "
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

        await ctx.respond(f"__**{user.display_name}'s Heroes:**__")
        await ctx.channel.send(hero_str)

    async def find(
            self, ctx: ApplicationContext,
            hero: str,
            mentions: Option(bool, "displays users as mentions",
                             required=False) = True
    ):
        """Finds all users with a particular hero"""
        try:
            hero = self.bot.heromatcher.match(hero)
        except ValueError as e:
            await ctx.respond(e.args[0], ephemeral=True)
            return

        await ctx.defer()

        discord_ids = self.bot.coop_db.fetch_flatten(f"""
            SELECT id FROM heroes_owned WHERE hero={hero.id}
        """)

        embed = Embed(color=0x99ff24,
                      title=f"Users of {hero.gamename}")

        # do pings, otherwise member names
        members = map(lambda x: ctx.guild.get_member(x), discord_ids)
        members = [x for x in members if x]
        if mentions:
            members = map(lambda x: x.mention, members)
            embed.description = ', '.join(members)
        else:
            members = map(lambda x: x.display_name, members)
            embed.description = '\n'.join(members)

        await ctx.respond(embed=embed)
