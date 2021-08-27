import aiocron
import asyncio
from collections import defaultdict
from dateparser import parse as parsedate
from datetime import datetime as dt
from datetime import timedelta
from discord import Member
from discord.ext import commands
from discord_slash import SlashContext
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option


class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.DATE_FORMAT = r"%d/%m/%Y %H:%M:%S"

        self.bot.bot.add_cog(self)

        self.update().start()

    async def remind(self, reminder_id: int, time: timedelta):
        async def _coro():
            await asyncio.sleep(time.total_seconds())

            if not (tup := self.bot.db.fetch(
                "SELECT uid, message, link FROM reminders "
                "WHERE id = %s", (reminder_id,)
            )):
                return

            uid, message, link = tup[0]

            await self.bot.bot.get_user(uid).send(
                f"<@{uid}> **REMINDER:** {message}\n\n Context: {link}"
            )

            self.bot.db.execute("DELETE FROM reminders WHERE id = %s",
                                (reminder_id,))

        asyncio.create_task(_coro())

    @cog_ext.cog_slash(
        name="remind",
        description="Reminds you about something.",
        options=[
            create_option("time", "When should the reminder be?",
                          str, True),
            create_option("message", "Message to include in the reminder.",
                          str, False)
        ]
    )
    async def reminder(self, ctx: SlashContext, time: str,
                       message: str = 'something'):
        time = parsedate('in ' + time)

        if time is None:
            await ctx.send(f"`{ctx.kwargs['time']}` is not a valid time.\n"
                           f"Example: `3h`, `08:05:00`, `07/09/2021 3pm`",
                           hidden=True)
            return

        delta = time - dt.now()
        if delta < timedelta(0):
            await ctx.send(f"You can't make a reminder to the past!",
                           hidden=True)
            return

        if len(message) > 199:
            await ctx.send("Message length must not exceed 200 characters!",
                           hidden=True)
            return

        await ctx.defer()

        reminder_id = self.bot.db.fetch("INSERT INTO reminders "
                                        "(uid, time, message, link) VALUES "
                                        "(%s, %s, %s, %s) RETURNING id",
                                        (ctx.author_id, time, message,
                                         ''))[0][0]

        # This does cause some potential overlap, but overlaps will happen
        # with bot restarts/reconnects
        if delta < timedelta(hours=1):
            await self.remind(reminder_id, delta)

        await ctx.send(f"Your reminder for **{message}** has been set for "
                       f"__{time.strftime(self.DATE_FORMAT)}__.")

        self.bot.db.execute("UPDATE reminders SET link = %s WHERE id = %s",
                            (ctx.message.jump_url, reminder_id))

    def update(self):
        @aiocron.crontab("0 * * * *")
        async def wrapper():
            reminders = self.bot.db.fetch(
                "SELECT id, time - NOW() FROM reminders "
                "WHERE time - NOW() < INTERVAL '1 hour'"
            )

            for reminder in reminders:
                await self.remind(*reminder)

        return wrapper


class Impersonation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.cooldowns = defaultdict(lambda: [dt.utcnow(), 3])

        self.bot.bot.add_cog(self)

    @cog_ext.cog_slash(
        name="impersonate",
        description="Speaks on behalf of someone else. (Limit: 4/20min)",
        options=[
            create_option(
                name='user',
                description='Who',
                option_type=Member,
                required=True
            ),
            create_option(
                name='message',
                description='What',
                option_type=str,
                required=True
            )
        ]
    )
    async def impersonate(self, ctx: SlashContext, user: Member, message: str):
        td = dt.utcnow() - self.cooldowns[user][0]
        self.cooldowns[user][0] = dt.utcnow()
        self.cooldowns[user][1] += td.total_seconds() / 300
        self.cooldowns[user][1] = min(4, self.cooldowns[user][1])

        if self.cooldowns[user][1] < 1 and ctx.author_id != 330509305663193091:
            cd = (1 - self.cooldowns[user][1]) * 300
            await ctx.send(f"This command is on cooldown for another {cd}s.",
                           hidden=True)
            return

        self.cooldowns[user][1] -= 1

        webhooks = await ctx.channel.webhooks()

        if not webhooks:
            webhook = await ctx.channel.create_webhook(
                name='VegeBot',
            )
        else:
            webhook = webhooks[0]

        await webhook.send(
            content=message,
            username=user.display_name,
            avatar_url=user.avatar_url
        )

        await ctx.send("Done", hidden=True)
