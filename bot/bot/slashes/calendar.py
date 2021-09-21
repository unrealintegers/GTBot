import asyncio
from datetime import datetime as dt
from datetime import timedelta

import aiocron
from dateparser import parse as parsedate
from discord import ApplicationContext, Option

from ..bot import DiscordBot, SlashCommand


class Reminder(SlashCommand, name="remind"):
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        super().__init__(bot, guild_ids)

        self.DATE_FORMAT = r"%d/%m/%Y %H:%M:%S"

        self.bot.bot.slash_command(guild_ids=self.guild_ids)(self.reminder)

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

    async def reminder(
            self, ctx: ApplicationContext,
            time: Option(str, "time of reminder (can be duration)"),
            message: Option(str, "message", required=False) = 'something'
    ):
        """Reminds you about something"""
        remind_time = parsedate('in ' + time)

        if remind_time is None:
            await ctx.respond(f"`{time}` is not a valid time.\n"
                              f"Example: `3h`, `08:05:00`, `07/09/2021 3pm`",
                              ephemeral=True)
            return

        delta = remind_time - dt.now()
        if delta < timedelta(0):
            await ctx.respond(f"You can't make a reminder to the past!",
                              ephemeral=True)
            return

        if len(message) > 199:
            await ctx.respond("Message length must not exceed 200 characters!",
                              ephemeral=True)
            return

        await ctx.defer()

        reminder_id = self.bot.db.fetch("INSERT INTO reminders "
                                        "(uid, time, message, link) VALUES "
                                        "(%s, %s, %s, %s) RETURNING id",
                                        (ctx.user.id, remind_time, message,
                                         ''))[0][0]

        # This does cause some potential overlap, but overlaps will happen
        # with bot restarts/reconnects
        if delta < timedelta(hours=1):
            await self.remind(reminder_id, delta)

        await ctx.respond(f"Your reminder for **{message}** has been set for "
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

