from datetime import datetime as dt
from typing import List

import discord
from discord import ApplicationContext

from ..bot import DiscordBot, SlashCommand
from ..utils import BackupChannel


class ChannelSlash(SlashCommand):
    def __init__(self, bot: DiscordBot, guild_ids: List[int]):
        super().__init__(bot, guild_ids)

        self.register(self.create_bot_channel)

        self.vege = self.bot.bot.get_guild(762888327161708615)

        if not self.vege:
            return

        # Category
        self._backup = self.vege.get_channel(837963878725976085)

        _channels = [ch for ch in self._backup.channels if "bot" in ch.name]

        everyone = self.vege.default_role
        bot_role = self.vege.get_role(827538975203262504)
        bots = self.vege.get_role(806083687866957884)
        admin = self.vege.get_role(812998213543133204)
        overwrites = {
            everyone: discord.PermissionOverwrite(
                read_messages=False
            ),
            bot_role: discord.PermissionOverwrite(
                read_messages=True
            ),
            bots: discord.PermissionOverwrite(
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
        self._users[ctx.user.id] = dt.utcnow()
        backup = self.get_next_channel()

        if not backup:
            return f"There are no more channels available."

        actives = list(filter(lambda b: b.active, self._backups))
        if not actives:
            pos = [self.vege.get_channel(806834639675195422).position]
        else:
            pos = map(lambda b: b.channel.position, actives)

        await backup.enable(max(pos) + 1)
        await backup.channel.send(f"<@{ctx.user.id}>")
        return f"<#{backup.channel.id}> has been created for you."

    async def create_bot_channel(self, ctx: ApplicationContext):
        bot_role = self.vege.get_role(827538975203262504)
        if bot_role not in ctx.user.roles and not \
                ctx.user.guild_permissions.administrator:
            await ctx.respond("You do not have permission "
                              "to use this command!",
                              ephemeral=True)
            return

        if ctx.user.id in self._users:
            cooldown = dt.utcnow() - self._users[ctx.user.id]
            if cooldown.total_seconds() > 3600 or \
                    ctx.user.guild_permissions.administrator:
                msg = await self.enable_next_channel(ctx)
                await ctx.respond(msg, ephemeral=True)
                return
            else:
                await ctx.respond(f"This command is on cooldown "
                                  f"for {cooldown}",
                                  ephemeral=True)
                return
        else:
            msg = await self.enable_next_channel(ctx)
            await ctx.respond(msg, ephemeral=True)
            return
