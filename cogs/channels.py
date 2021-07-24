import discord
from datetime import datetime as dt
from discord.ext import commands
from discord_slash import SlashContext
from discord_slash import cog_ext

from .utils import BackupChannel


class ChannelSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self._backup = self.bot.Vege.get_channel(837963878725976085)

        _channels = [ch for ch in self._backup.channels if "bot" in ch.name]

        everyone = self.bot.Vege.default_role
        bot_role = self.bot.Vege.get_role(827538975203262504)
        bot = self.bot.Vege.get_role(806083687866957884)
        admin = self.bot.Vege.get_role(812998213543133204)
        overwrites = {
            everyone: discord.PermissionOverwrite(
                read_messages=False
            ),
            bot_role: discord.PermissionOverwrite(
                read_messages=True
            ),
            bot: discord.PermissionOverwrite(
                read_messages=True
            ),
            admin: discord.PermissionOverwrite(
                manage_permissions=False
            )
        }

        _channels.sort(key=lambda ch: ch.name)

        self._backups = [BackupChannel(ch, 1200, overwrites,
                                       category_id=806834564575002624)
                         for ch in _channels]

        self._users = {}

    def get_next_channel(self):
        chs = list(filter(lambda ch: ch.channel.category == self._backup,
                          self._backups))
        if chs:
            return chs[0]

        return None

    async def enable_next_channel(self, ctx):
        self._users[ctx.author_id] = dt.utcnow()
        backup = self.get_next_channel()

        if not backup:
            return f"There are no more channels available."

        actives = list(filter(lambda b: b.active, self._backups))
        if not actives:
            pos = [self.bot.Vege.get_channel(806834639675195422).position]
        else:
            pos = map(lambda b: b.channel.position, actives)

        await backup.enable(max(pos) + 1)
        await backup.channel.send(f"<@{ctx.author_id}>")
        return f"<#{backup.channel.id}> has been created for you."

    @cog_ext.cog_slash(guild_ids=[762888327161708615],
                       name="createbotchannel",
                       description="Creates a new temporary bot channel.",
                       )
    async def create_bot_channel(self, ctx: SlashContext):
        bot_role = self.bot.Vege.get_role(827538975203262504)
        if bot_role not in ctx.author.roles and not \
                ctx.author.guild_permissions.administrator:
            await ctx.send("You do not have permission to use this command!",
                           hidden=True)
            return

        if ctx.author_id in self._users:
            cooldown = dt.utcnow() - self._users[ctx.author_id]
            if cooldown.total_seconds() > 3600 or \
                    ctx.author.guild_permissions.administrator:
                msg = await self.enable_next_channel(ctx)
                await ctx.send(msg, hidden=True)
                return
            else:
                await ctx.send(f"This command is on cooldown for {cooldown}",
                               hidden=True)
                return
        else:
            msg = await self.enable_next_channel(ctx)
            await ctx.send(msg, hidden=True)
            return
