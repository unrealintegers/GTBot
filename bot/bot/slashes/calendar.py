import asyncio
from datetime import datetime as dt
from datetime import timedelta
from enum import Enum
from typing import List, NamedTuple

import aiocron
from dateparser import parse as parsedate
from discord import ApplicationContext, Option

from ..bot import DiscordBot, SlashCommand


class Reminder(SlashCommand, name="remind"):
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        super().__init__(bot, guild_ids)

        self.DATE_FORMAT = r"%d/%m/%Y %H:%M:%S"

        self.bot.bot.slash_command(name='remind',
                                   guild_ids=self.guild_ids)(self.reminder)

        self.update().start()

    async def remind(self, reminder_id: int, time: timedelta):
        async def _coro():
            await asyncio.sleep(time.total_seconds())

            if not (tup := self.bot.db.fetch(
                    "SELECT * FROM reminders WHERE id = %s",
                    (reminder_id,)
            )):
                return

            r = tup[0]
            if r.repeats > 0:
                next_time = r.time + r.repeat_interval
                self.bot.db.execute(
                    "INSERT INTO reminders "
                    "(uid, time, message, link, repeats, repeat_interval) "
                    "VALUES (%s, %s, %s, %s, %s, %s) ",
                    (r.uid, next_time, r.message,
                     r.link, r.repeats - 1, r.repeat_interval)
                )

                await self.bot.bot.get_user(r.uid).send(
                    f"<@{r.uid}> **REMINDER:** {r.message}\n\n"
                    f"Context: {r.link}\n\n"
                    f"Repeats Remaining: {r.repeats}\n"
                    f"Next Reminder: <t:{int(next_time.timestamp())}>"
                )

            elif r.repeats == -1:
                next_time = r.time + r.repeat_interval
                self.bot.db.execute(
                    "INSERT INTO reminders "
                    "(uid, time, message, link, repeats, repeat_interval) "
                    "VALUES (%s, %s, %s, %s, %s, %s) ",
                    (r.uid, next_time, r.message,
                     r.link, -1, r.repeat_interval)
                )

                await self.bot.bot.get_user(r.uid).send(
                    f"<@{r.uid}> **REMINDER:** {r.message}\n\n"
                    f"Context: {r.link}\n\n"
                    f"Next Reminder: <t:{next_time.timestamp()}>"
                )

            else:
                await self.bot.bot.get_user(r.uid).send(
                    f"<@{r.uid}> **REMINDER:** {r.message}\n\n"
                    f"Context: {r.link}"
                )

            self.bot.db.execute("DELETE FROM reminders WHERE id = %s",
                                (reminder_id,))

        asyncio.create_task(_coro())

    async def reminder(
            self, ctx: ApplicationContext,
            time: Option(str, "time of reminder (can be duration)"),
            message: Option(str, "message", required=False) = 'something',
            repeats: Option(int, "-1 for infinity, defaults to 0",
                            required=False) = 0,
            interval: Option(str, "repeat interval, defaults tp reminder time",
                             required=False) = None
    ):
        """Reminds you about something"""
        repeat = (repeats == 0)

        if repeat < -1:
            await ctx.respond("Repeat has to be -1, 0 or a positive integer!",
                              ephemeral=True)

        remind_time = parsedate('in ' + time)

        if remind_time is None:
            await ctx.respond(f"`{time}` is not a valid time.\n"
                              f"Example: `3h`, `08:05:00`, `07/09/2021 3pm`",
                              ephemeral=True)
            return

        delta = remind_time - dt.now()
        if delta < timedelta(0):
            await ctx.respond("You can't make a reminder to the past!",
                              ephemeral=True)
            return

        if len(message) > 199:
            await ctx.respond("Message length must not exceed 200 characters!",
                              ephemeral=True)
            return

        await ctx.defer()

        if interval:
            interval = parsedate("in " + interval) - dt.now()
        else:
            interval = delta

        if interval < timedelta(hours=2):
            await ctx.respond("Repeat interval has to be longer than 2h!",
                              ephemeral=True)

        reminder_id = self.bot.db.fetch(
            "INSERT INTO reminders "
            "(uid, time, message, link, repeats, repeat_interval) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "RETURNING id",
            (ctx.user.id, remind_time, message, '', repeats, interval)
        )[0][0]

        # This does cause some potential overlap, but overlaps will happen
        # with bot restarts/reconnects
        if delta < timedelta(hours=1):
            await self.remind(reminder_id, delta)

        response = await ctx.respond(
            f"Your reminder for **{message}** has been set for "
            f"<t:{int(remind_time.timestamp())}>."
        )

        self.bot.db.execute("UPDATE reminders SET link = %s WHERE id = %s",
                            (response.jump_url, reminder_id))

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


class RepeatDay(Enum):
    NO_EVENT = '0'
    NEW_EVENT = '+'
    NEW_ROUND = '/'
    ONGOING_ROUND = '-'


class Event:
    def __init__(self, name: str, start_time: dt,
                 repeat: List[RepeatDay], unit_interval: timedelta,
                 max_repeats: int, fmt: str,
                 **_):  # discord extra kwargs
        self.name = name
        self.start_time = start_time
        self.repeat = repeat
        self.max_repeats = max_repeats

        self._format = fmt

        now = dt.now().astimezone()

        # self.has_rounds = RepeatDay.NEW_ROUND in self.repeat
        cycle_length = len(repeat)
        interval = unit_interval * cycle_length

        # Number of repeats since event started
        self.repeats = (now - start_time) // interval
        self.active = True
        if self.repeats > self.max_repeats != -1:
            self.active = False
            return

        # Start of current repeat
        repeat_start = start_time + self.repeats * interval

        # This is the index we want out of the repeat list
        index = (now - repeat_start) // unit_interval
        if repeat[index] is RepeatDay.NO_EVENT:
            self.active = False
            return

        # We look for end of this round and cycle
        self.round_end, self.cycle_end = None, None
        for idx, day in list(enumerate(repeat))[index + 1:]:
            if not self.cycle_end and day is RepeatDay.NO_EVENT:
                self.cycle_end = idx
            if not self.round_end and \
                    (day is RepeatDay.NEW_ROUND or day is RepeatDay.NO_EVENT):
                self.round_end = idx
            if self.cycle_end and self.round_end:
                break
        self.round_end = self.round_end or index + 1
        self.cycle_end = self.cycle_end or index + 1

        # And now we look for start of this round and cycle
        self.round_start, self.cycle_start = None, None
        for idx, day in list(enumerate(repeat))[index - 1::-1]:
            if not self.cycle_start and day is RepeatDay.NEW_EVENT:
                self.cycle_start = idx
            if not self.round_start and \
                    (day is RepeatDay.NEW_ROUND or day is RepeatDay.NEW_EVENT):
                self.round_start = idx
            if self.cycle_start and self.round_start:
                break

        # Number of round
        self.round_num = repeat[self.cycle_start:index + 1] \
                             .count(RepeatDay.NEW_ROUND) + 1  # noqa
        self.total_round = repeat[self.cycle_start:self.cycle_end + 1] \
                               .count(RepeatDay.NEW_ROUND) + 1  # noqa

        # Calculate current day and total length
        self.cycle_day = index - self.cycle_start + 1
        self.round_day = index - self.round_start + 1
        self.cycle_length = self.cycle_end - self.cycle_start
        self.round_length = self.round_end - self.round_start

        # Convert back to datetime
        self.round_start = repeat_start + unit_interval * self.round_start
        self.round_end = repeat_start + unit_interval * self.round_end
        self.cycle_start = repeat_start + unit_interval * self.cycle_start
        self.cycle_end = repeat_start + unit_interval * self.cycle_end

    def __str__(self):
        formats = {
            "n": self.name,
            "rs": int(self.round_start.timestamp()),
            "re": int(self.round_end.timestamp()),
            "rd": self.round_day,
            "rl": self.round_length,
            "rn": self.round_num,
            "rt": self.total_round,
            "cs": int(self.cycle_start.timestamp()),
            "ce": int(self.cycle_end.timestamp()),
            "cd": self.cycle_day,
            "cl": self.cycle_length
        }
        return self._format.format(**formats)

    @staticmethod
    def from_db(row: NamedTuple):
        row = row._asdict()  # noqa, underscore method
        row['repeat'] = list(map(RepeatDay, row['repeat']))
        row['fmt'] = row['format']
        del row['format']
        return Event(**row)


class Events(SlashCommand, name="events"):
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        super().__init__(bot, guild_ids)

        self.events = bot.bot.command_group(
            "events", "No Description", guild_ids=self.guild_ids
        )

        self.events.command(guild_ids=self.guild_ids)(self.list)

    async def list(self, ctx: ApplicationContext):
        """Shows a list of events"""
        await ctx.defer(ephemeral=True)

        events = self.bot.db.fetch("SELECT * FROM events")

        events = map(Event.from_db, events)
        active_events = filter(lambda e: e.active, events)
        events_str = '\n\n'.join(map(str, active_events))
        await ctx.respond(events_str, ephemeral=True)
