from __future__ import annotations

import typing
from datetime import datetime as dt

from discord import HTTPException, Forbidden, NotFound
from discord import Interaction, InteractionType
from discord import Member, Embed, TextChannel, Message, Guild
from discord.enums import OptionType

from .utils import discord_escape

if typing.TYPE_CHECKING:
    from .bot import DiscordBot


class Listeners:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        self.log_guild = bot.bot.get_guild(839860394051108864)

        # Logging listeners
        bot.bot.add_listener(self.member_action("joined"), "on_member_join")
        bot.bot.add_listener(self.member_action("left"), "on_member_remove")
        bot.bot.add_listener(self.message_remove(), "on_message_delete")

        # We have to do this using a bot.event since it gets called before
        # the command is processed
        bot.bot.event(self.interact())

    async def parse_option(self, opt, guild: typing.Optional[Guild]) \
            -> typing.Optional[str]:
        if opt['type'] == OptionType.user.value:
            if guild:
                getters = (guild.get_member,)
                fetchers = (guild.fetch_member,)
            else:
                getters = (self.bot.bot.get_user,)
                fetchers = (self.bot.bot.fetch_user,)
        elif opt['type'] == OptionType.channel.value:
            getters = (guild.get_channel,)
            fetchers = (guild.fetch_channel,)
        elif opt['type'] == OptionType.role.value:
            getters = (guild.get_role,)
            fetchers = tuple()
        elif opt['type'] == OptionType.mentionable.value:
            getters = (guild.get_member, guild.get_role)
            fetchers = (guild.fetch_member,)
        elif opt['type'] in (OptionType.string.value,
                             OptionType.integer.value,
                             OptionType.boolean.value):
            return f"`<{opt['name']} = {opt['value']}>`"
        else:
            return

        # Try each getter/fetcher sequentially until one works
        for getter in getters:
            # These Union[...] gives warnings
            if res := getter(opt['value']):  # noqa
                return f"`<{opt['name']} = {res}>`"
        for fetcher in fetchers:
            if res := await fetcher(opt['value']):  # noqa
                return f"`<{opt['name']} = {res}>`"
        return f"`<{opt['name']} = {opt['value']}>`"

    def get_channel(self, cid: int) -> TextChannel:
        return self.log_guild.get_channel(cid)

    def member_action(self, event: str):
        channel = self.get_channel(849870406945079297)

        async def wrapper(member: Member):
            # Auto-roles
            if member.guild.id == 762888327161708615:
                if member.id in [490756819401179138]:
                    await member.ban(delete_message_days=0)
                    return
                await member.add_roles(
                    member.guild.get_role(809270443029561354))

            # Logging
            embed = Embed(colour=0x12ffc8,
                          description=f"**Discord Tag:** `{member}`\n"
                                      f"**ID:** `{member.id}`")
            embed.set_footer(text=dt.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            embed.set_author(name=f"{member.display_name} has {event} "
                                  f"{member.guild.name}.",
                             icon_url=member.avatar.url)

            await channel.send(embed=embed)

        return wrapper

    def message_remove(self):
        channel = self.get_channel(849882469687492618)

        async def wrapper(msg: Message):
            content = discord_escape(msg.content)
            member = msg.author

            embed = Embed(colour=0x12ffc8, description=content)
            embed.set_footer(text=dt.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            embed.set_author(name=f"Message by {member.display_name} was "
                                  f"deleted.",
                             icon_url=member.avatar.url)
            embed.add_field(name="\u200B",
                            value=f"Channel: {msg.channel.mention}")
            await channel.send(embed=embed)

            if msg.attachments:
                for attach in msg.attachments:
                    try:
                        file = await attach.to_file(use_cached=True)
                        await channel.send(file=file)
                    except (HTTPException, Forbidden, NotFound):
                        await channel.send(f"`<Deleted attachment "
                                           f"{attach.filename}>`")

        return wrapper

    def interact(self):
        channel = self.get_channel(852365427299975208)

        async def on_interaction(interaction: Interaction):
            # We only want slash commands
            if interaction.type is InteractionType.application_command:
                # Get the command's name
                data = (interaction.data,)
                cmd = '/'

                while 'name' in data[0] and 'options' in data[0]:
                    cmd += data[0]['name'] + ' '
                    data = data[0]['options']

                if data[0]['type'] in (OptionType.sub_command.value,
                                       OptionType.sub_command_group.value):
                    cmd += data[0]['name'] + ' '

                # Get the arguments of the command
                user = interaction.user
                guild = interaction.guild

                args = [await self.parse_option(arg, guild) for arg in data]
                args = filter(lambda x: x is not None, args)

                # Construct an embed and send
                embed = Embed(colour=0x12ffc8)
                embed.description = f"{cmd}{'  '.join(args)}"
                embed.set_footer(
                    text=dt.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
                embed.set_author(name=f"{user} used command {cmd}",
                                 icon_url=user.avatar.url)
                await channel.send(embed=embed)

            await self.bot.bot.process_application_commands(interaction)

        return on_interaction
