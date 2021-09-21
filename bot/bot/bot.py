from __future__ import annotations

import os

import discord
from discord.ext import commands

from .listeners import Listeners
from .manager import GuildCommandManager
from .reaction import ReactionListener  # TODO: Consider merging listeners?
from .utils import DatabaseConnection, HeroMatcher


class SlashCommand:
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        self.bot = bot
        self.guild_ids = guild_ids

    def __init_subclass__(cls, **kwargs):
        if 'name' in kwargs:
            cls.name = kwargs['name']
        else:
            cls.name = cls.__name__.lower()


class DiscordBot:
    def __init__(self, prefix: str):
        self.bot = commands.Bot(command_prefix=prefix,
                                intents=discord.Intents.all())

        self.bot.remove_command('help')

        self.manager = GuildCommandManager(self)
        self.cogs = {}

        self.db = DatabaseConnection(os.getenv("BOT_DATABASE_URL"))
        self.coop_db = DatabaseConnection(os.getenv("COOP_DATABASE_URL"))
        self.heromatcher = HeroMatcher(self.coop_db)

        self.bot.add_listener(self.on_ready)

    async def instantiate_commands(self, cmd_dict):
        for sub_cls in SlashCommand.__subclasses__():
            name = sub_cls.name  # noqa : name is guaranteed to be defined
            guild_ids = cmd_dict.pop(name, None)  # None = global
            sub_cls(self, guild_ids)

        if cmd_dict:
            print(f"Unregistered Commands: {cmd_dict}")

    def run(self):
        self.bot.run(os.getenv("BOT_TOKEN"))

    async def on_ready(self):
        print("Connected")

        self.bot.add_cog(self.manager)

        Listeners(self)
        ReactionListener(self)

        await self.instantiate_commands(self.manager.get_commands())

        await self.bot.register_commands()

        print("Synced")
