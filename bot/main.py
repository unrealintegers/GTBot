import discord
import os
from discord.ext import commands
from discord_slash import SlashCommand

from cogs import *
from cogs.utils import DatabaseConnection, HeroMatcher


class Bot:
    def __init__(self, prefix: str):
        self.bot = commands.Bot(command_prefix=prefix,
                                intents=discord.Intents.all())
        self.slash = SlashCommand(self.bot, override_type=True,
                                  sync_commands=False)

        self.bot.remove_command('help')

        self.db = DatabaseConnection(os.getenv("BOT_DATABASE_URL"))
        self.coop_db = DatabaseConnection(os.getenv("COOP_DATABASE_URL"))
        self.heromatcher = HeroMatcher(self.coop_db)

        # Should make these into a cog too
        self.bot.add_listener(self.on_ready)
        self.bot.add_listener(self.on_resumed)
        self.bot.add_listener(self.on_member_join)
        self.bot.add_listener(self.on_disconnect)

    def run(self):
        self.bot.run(os.getenv("BOT_TOKEN"))

    async def on_ready(self):
        print("Connected")

        admin.Evaluate(bot)
        admin.PurgeCommand(bot)
        general.Reminder(bot)
        general.Impersonation(bot)
        gtutil.Stamina(bot)
        gtutil.WeekCheck(bot)
        logging.Logging(bot)

        # self.bot.add_cog(channels.ChannelSlash(self))
        self.bot.add_cog(coop.CoopSlash(self))
        self.bot.add_cog(cog := cogs.CogCommand(self))
        self.bot.add_cog(reaction.ReactionListener(self))

        cron.Cron(bot)

        # vh = vegehints.Vegehints(bot)
        # self.bot.add_cog(vh)
        # await vh.init_vegehints()

        cog.sync_cmds()

        await self.slash.sync_all_commands()

    async def on_resumed(self):
        print("Reconnected")

    async def on_member_join(self, member):
        if member.guild.id == 762888327161708615:
            await member.add_roles(member.guild.get_role(809270443029561354))

    async def on_disconnect(self):
        print("Disconnected")


if __name__ == "__main__":
    bot = Bot(',')
    bot.run()
