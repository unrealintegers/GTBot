import discord
import os
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import *

from cogs import *


# logger = py_logging.getLogger('discord')
# logger.setLevel(py_logging.WARNING)
# handler = py_logging.FileHandler(filename='discord.log', encoding='utf-8',
#                                  mode='w')
# handler.setFormatter(
#     py_logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)


class Bot:
    def __init__(self, prefix: str):
        self.bot = commands.Bot(command_prefix=prefix,
                                intents=discord.Intents.all())
        self.Vege = None
        self.slash = SlashCommand(self.bot, override_type=True)

        self.bot.remove_command('help')

        # Should make these into a cog too
        self.bot.add_listener(self.on_ready)
        self.bot.add_listener(self.on_resumed)
        self.bot.add_listener(self.on_member_join)
        self.bot.add_listener(self.on_disconnect)

    def run(self):
        self.bot.run(os.getenv("BOT_TOKEN"))

    async def on_ready(self):
        print("Connected")

        self.Vege = self.bot.get_guild(762888327161708615)

        general.Impersonation(bot)
        general.Evaluate(bot)
        general.Reminder(bot)
        gtutil.Stamina(bot)

        self.bot.add_cog(channels.ChannelSlash(self))
        self.bot.add_cog(coop.CoopSlash(self))
        self.bot.add_cog(purge.PurgeCommand(self))
        self.bot.add_cog(reaction.ReactionListener(self))
        self.bot.add_cog(roll.RollCommand(self))
        self.bot.add_cog(weather.WeatherCommand(self))

        vh = vegehints.Vegehints(bot)
        cron.Cron(bot)
        logging.Logging(bot)

        # discord_log = logging.Logging(bot)

        self.bot.add_cog(vh)
        await vh.init_vegehints()

        # Only select guilds which bot is in
        guild_ids = [g.id for g in self.bot.guilds]
        for name, cmd in self.slash.commands.items():
            cmd.allowed_guild_ids = [x for x in cmd.allowed_guild_ids
                                     if x in guild_ids]

            for subcmd in self.slash.subcommands[name].values():
                subcmd.allowed_guild_ids = [x for x in subcmd.allowed_guild_ids
                                            if x in guild_ids]

        await self.slash.sync_all_commands()

    async def on_resumed(self):
        print("Reconnected")
        asyncio.create_task(self.bot.get_cog("CoopSlash")
                            .backup.check_activity())

    async def on_member_join(self, member):
        if member.guild.id == 762888327161708615:
            await member.add_roles(self.Vege.get_role(809270443029561354))

    async def on_disconnect(self):
        print("Disconnected")


if __name__ == "__main__":
    bot = Bot(',')
    bot.run()
