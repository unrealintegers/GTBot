from dateparser import parse as parsedate
from datetime import datetime as dt
from datetime import timedelta
from discord.ext import commands
from discord_slash.cog_ext import cog_slash
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option


class Stamina(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.DATE_FORMAT = r"%d/%m/%Y %H:%M:%S"

        self.bot.bot.add_cog(self)

    @cog_slash(
        name='stamcalc',
        description='Calculates how much GT stamina '
                    'you will have at a certain time',
        options=[
            create_option('time', 'Can be interval (1h3m) or exact (8pm)',
                          str, True),
            create_option('current', 'Your current stamina', int, False)
        ]
    )
    async def stamcalc(self, ctx: SlashContext,
                       time: str, current: int = None):

        time = parsedate('in ' + time)
        if time is None:
            await ctx.send(f"`{ctx.kwargs['time']}` is not a valid time.\n"
                           f"Example: `3h`, `08:05:00`, `07/09/2021 3pm`",
                           hidden=True)
            return

        delta = time - dt.now()

        if delta < timedelta(0):
            await ctx.send(f"`time` cannot be in the past!", hidden=True)
            return

        regen = delta.total_seconds() / 60 / 10

        if current is None:
            await ctx.send(f"You will regenerate **{regen:.1f}** stamina "
                           f"before `{time.strftime(self.DATE_FORMAT)}`",
                           hidden=True)
            return
        else:
            total = regen + current

            if total <= 72:
                await ctx.send(f"You will have **{total:.1f}** stamina at "
                               f"`{time.strftime(self.DATE_FORMAT)}`",
                               hidden=True)
            else:
                await ctx.send(f"You will have **76** stamina at "
                               f"`{time.strftime(self.DATE_FORMAT)}`. "
                               f"{total - 76:.1f} stamina will be wasted!",
                               hidden=True)
