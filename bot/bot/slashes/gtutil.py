from datetime import datetime as dt
from datetime import timedelta

from dateparser import parse as parsedate
from discord import ApplicationContext, Option

from ..bot import DiscordBot, SlashCommand


class Stamina(SlashCommand, name="stamcalc"):
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        super().__init__(bot, guild_ids)

        self.DATE_FORMAT = r"%d/%m/%Y %H:%M:%S"

        self.register(self.stamcalc)

    async def stamcalc(
            self, ctx: ApplicationContext,
            time: Option(str, "date, time or duration"),
            current: Option(int, "your current stamina", required=False) = None
    ):
        """Calculates how much stamina you will have at a specific time
        for Guardian Tales"""
        dur = parsedate('in ' + time)
        if dur is None:
            await ctx.respond(f"`{time}` is not a valid time.\n"
                              f"Example: `3h`, `08:05:00`, `07/09/2021 3pm`",
                              ephemeral=True)
            return

        delta = dur - dt.now()

        if delta < timedelta(0):
            await ctx.respond(f"`time` cannot be in the past!", ephemeral=True)
            return

        regen = delta.total_seconds() / 60 / 10

        if current is None:
            await ctx.respond(f"You will regenerate **{regen:.1f}** stamina "
                              f"before `{dur.strftime(self.DATE_FORMAT)}`",
                              ephemeral=True)
            return
        else:
            total = regen + current

            if total <= 72:
                await ctx.respond(f"You will have **{total:.1f}** stamina at "
                                  f"`{dur.strftime(self.DATE_FORMAT)}`",
                                  ephemeral=True)
            else:
                await ctx.respond(f"You will have **76** stamina at "
                                  f"`{dur.strftime(self.DATE_FORMAT)}`. "
                                  f"{total - 76:.1f} stamina will be wasted!",
                                  ephemeral=True)


class WeekCheck(SlashCommand):
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        super().__init__(bot, guild_ids)

        self.register(self.weekcheck)

    async def weekcheck(self, ctx: ApplicationContext):
        """Checks what week this is"""
        start_date = dt(2021, 7, 25, 14, 0, 0)
        week_seconds = 7 * 24 * 60 * 60

        weeks = (dt.utcnow() - start_date).total_seconds() // week_seconds

        if weeks % 2 == 0:
            await ctx.respond(f"Arena (Yellow) Week", ephemeral=True)
        else:
            await ctx.respond(f"Co-op (Green) Week", ephemeral=True)
