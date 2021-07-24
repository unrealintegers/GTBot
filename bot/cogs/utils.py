import asyncio
import discord
from collections import defaultdict
from datetime import datetime as dt


def discord_escape(msg):
    return msg.replace("_", r"\_").replace("*", r"\*")\
        .replace("`", r"\`").replace("@", "@\u200B").replace("~", r"\~")


def convert_args(args):
    args = ['-_'] + list(args)
    tree = defaultdict(lambda: None)
    parents = [i for i in range(len(args)) if args[i][0] == '-']
    parents.append(len(args))  # Add upper search limit
    for i in range(len(parents) - 1):
        arg = ' '.join(args[parents[i] + 1: parents[i + 1]])
        if args[parents[i]][1:] in tree:
            tree[args[parents[i]][1:]].append(arg)
        else:
            tree[args[parents[i]][1:]] = [arg]
    return tree


class Hero:
    def __init__(self, title, name):
        self.gamename = f"{title} {name}".strip()
        title = title.lower()
        name = name.lower()
        self.name = name
        self.fullname = f"{title} {name}".strip()
        self.tokens = set(self.fullname.split())
        self.initials = ''.join(map(lambda x: x[0], self.fullname.split()))


class HeroMatcher:
    with open("heroes.txt") as f:
        h = f.read().split('\n')

    heroes = list(map(lambda x: Hero(*x.split(',')), h))

    members = {}  # member ID -> channel ID

    @classmethod
    def match(cls, txt):
        txt = txt.lower().strip()
        if ' ' not in txt:
            # Match hero name
            candidates = []
            for hero in cls.heroes:
                if hero.name.startswith(txt):
                    candidates.append(hero)

            if len(candidates) == 1:
                return candidates[0]
            elif len(candidates) >= 1:
                raise ValueError("Too many heroes found!")

            # Match initials
            for hero in cls.heroes:
                if hero.initials == txt:
                    candidates.append(hero)

            if len(candidates) == 1:
                return candidates[0]
            elif len(candidates) >= 1:
                raise ValueError("Too many heroes found!")
            else:
                raise ValueError("Hero not found!")

        else:
            words = set(txt.split())
            candidates = []
            for hero in cls.heroes:
                if words.issubset(hero.tokens):
                    candidates.append(hero)

            if len(candidates) == 1:
                return candidates[0]
            elif len(candidates) >= 1:
                raise ValueError("Too many heroes found!")
            else:
                raise ValueError("Hero not found!")


class BackupChannel:
    admin_id = 812998213543133204
    backup_id = 837963878725976085

    def __init__(self, channel, inactive_timeout, overwrites,
                 *, category_id):
        self.active = False

        self.channel = channel
        self._guild = channel.guild
        self.overwrites = overwrites

        self._timeout = inactive_timeout
        self._category_id = category_id

    async def enable(self, pos):
        await self.channel.edit(
            category=self._guild.get_channel(self._category_id),
            position=pos,
            reason="Enabling Overflow Channel",
            overwrites=self.overwrites
        )
        self.active = True

        asyncio.create_task(self.check_activity())

    async def check_activity(self):
        # Check every 60 secs
        await asyncio.sleep(60)

        msg = self.channel.last_message

        if msg is None:
            msg = (await self.channel.history(limit=1).flatten())[0]

        # Archive and hide again
        if (dt.utcnow() - msg.created_at).total_seconds() > self._timeout:

            if self.channel.category_id != BackupChannel.backup_id:
                everyone = self._guild.default_role
                admin = self._guild.get_role(BackupChannel.admin_id)
                await self.channel.edit(
                    category=self._guild.get_channel(BackupChannel.backup_id),
                    reason="Disabling Overflow Channel",
                    overwrites={
                        everyone: discord.PermissionOverwrite(
                            read_messages=False
                        ),
                        admin: discord.PermissionOverwrite(
                            manage_permissions=False
                        )
                    }
                )

                self.active = False

                return

        # If not, check again later
        asyncio.create_task(self.check_activity())


class ChannelManager:
    def __init__(self):
        pass
