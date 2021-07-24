import aiocron
import asyncio
import io
import json
from collections import defaultdict
from dateparser import parse as parsedate
from datetime import datetime as dt
from datetime import timedelta
from discord import Member, File
from discord.ext import commands
# from discord.utils import escape_markdown
from discord_slash import SlashContext
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option


class Evaluate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.result = None

        self.bot.bot.add_cog(self)

    @cog_ext.cog_slash(
        name="eval",
        description="evaluate",
        options=[
            create_option(
                name='command',
                description='What you want to do',
                option_type=str,
                required=False
            ),
        ]
    )
    async def _eval(self, ctx: SlashContext, command: str):
        if ctx.author.id not in [330509305663193091, 475440146221760512]:
            await ctx.send("What do you think you're doing?", hidden=True)
            return

        hidden = (command[0] == "&")
        if hidden:
            command = command[1:]

        if command[0] == command[-1] == '`':
            command = command[1:-1]

        if command.startswith("await "):
            command = command[6:]
            self.result = str(await eval(command))
        else:
            self.result = str(eval(command))

        if len(self.result) > 2000:
            fp = io.BytesIO(self.result.encode('utf-8'))
            await ctx.send(File(fp, "output.txt"))
        else:
            await ctx.send(self.result, hidden=hidden)


class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.DATE_FORMAT = r"%d/%m/%Y %H:%M:%S"

        self.bot.bot.add_cog(self)

        self.update().start()

    async def remind(self, uid: int, time: int, message: str, link: str):
        async def _coro():
            await asyncio.sleep(time)
            await self.bot.bot.get_user(uid).send(
                f"<@{uid}> **REMINDER:** {message}\n\n Context: {link}"
            )

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
        # tp = re.compile("^((?P<hours>\d+(?:\.\d+)?)(?:h|($)|(:)))?"
        #                 "(?(3)|(?P<minutes>\d+(?:\.\d+)?)(?:($)|(?(4)\4|m)))?"
        #                 "(?(6)|(?P<seconds>\d+(?:\.\d+)?)(?:$|(?(4)|s)))?"
        #                 "(?(2)$|(?(5)$|(?(7)$|(?!$))))")

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
        elif delta < timedelta(hours=1):
            await ctx.send(f"Your reminder for **{message}** has been set for "
                           f"__{time.strftime(self.DATE_FORMAT)}__.")
            await self.remind(ctx.author_id, int(delta.total_seconds()),
                              message, ctx.message.jump_url)
        else:
            with open('reminder.txt') as f:
                reminders = json.loads(f.read())

            await ctx.send(f"Your reminder for **{message}** has been set for "
                           f"__{time.strftime(self.DATE_FORMAT)}__.")

            reminders.append({'time': time.strftime(self.DATE_FORMAT),
                              'uid': ctx.author_id, 'message': message,
                              'link': ctx.message.jump_url})

            with open('reminder.txt', 'w') as f:
                f.write(json.dumps(reminders))

    def update(self):
        def check_if_soon(reminder):
            time = dt.strptime(reminder['time'], self.DATE_FORMAT)
            return time - dt.now() < timedelta(hours=1)

        @aiocron.crontab("0 * * * *")
        async def wrapper():
            with open('reminder.txt') as f:
                reminders = json.loads(f.read())

            remind_soon = list(filter(check_if_soon, reminders))
            remind_later = list(filter(lambda x: not check_if_soon(x),
                                       reminders))

            with open('reminder.txt', 'w') as f:
                f.write(json.dumps(remind_later))

            for reminder in remind_soon:
                time = dt.strptime(reminder['time'], self.DATE_FORMAT)
                reminder['time'] = time - dt.now()
                await self.remind(**reminder)

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
        print(self.cooldowns[user])

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
