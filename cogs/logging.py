import discord
from datetime import datetime as dt
from datetime import timedelta
from discord import Member, Embed, TextChannel, Message, AuditLogAction
from discord import HTTPException, Forbidden, NotFound
from discord_slash.context import SlashContext

from .utils import discord_escape


class Logging:
    def __init__(self, bot):
        self.bot = bot

        self.log_guild = bot.bot.get_guild(839860394051108864)

        bot.bot.add_listener(self.member_action("joined"), "on_member_join")
        bot.bot.add_listener(self.member_action("left"), "on_member_remove")
        bot.bot.add_listener(self.message_remove(), "on_message_delete")
        bot.bot.add_listener(self.slash_cmd(), "on_slash_command")

    def get_channel(self, cid: int) -> TextChannel:
        return self.log_guild.get_channel(cid)

    def member_action(self, event: str):
        channel = self.get_channel(849870406945079297)

        async def wrapper(member: Member):
            embed = Embed(colour=0x12ffc8,
                          description=f"**Discord Tag:** `{member}`\n"
                                      f"**ID:** `{member.id}`")
            embed.set_footer(text=dt.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            embed.set_author(name=f"{member.display_name} has {event} "
                                  f"{member.guild.name}.",
                             icon_url=member.avatar_url)

            await channel.send(embed=embed)

        return wrapper

    def message_remove(self):
        channel = self.get_channel(849882469687492618)

        async def wrapper(msg: Message):
            content = discord_escape(msg.content)
            member = msg.author

            async for al in msg.guild.audit_logs(
                    limit=5, after=dt.utcnow() - timedelta(seconds=10),
                    action=AuditLogAction.message_delete
            ):
                print(al)

            embed = Embed(colour=0x12ffc8, description=content)
            embed.set_footer(text=dt.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            embed.set_author(name=f"Message by {member.display_name} was "
                                  f"deleted.",
                             icon_url=member.avatar_url)
            embed.add_field(name="\u200B",
                            value=f"Channel: {msg.channel.mention}")
            await channel.send(embed=embed)

            if msg.attachments:
                for attach in msg.attachments:
                    try:
                        file = await attach.to_file(use_cached=True)
                        await channel.send(file=file)
                    except (HTTPException, Forbidden, NotFound):
                        await channel.send(f"<Deleted attachment "
                                           f"{attach.filename}>")

        return wrapper

    def slash_cmd(self):
        channel = self.get_channel(852365427299975208)

        async def wrapper(ctx: SlashContext):
            member = ctx.author

            embed = Embed(colour=0x12ffc8)
            embed.description = f"/{ctx.name} {ctx.subcommand_name or ''} " \
                                f"{' '.join(map(str, ctx.args))}"
            embed.set_footer(text=dt.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            embed.set_author(name=f"{member.display_name} used command "
                                  f"{ctx.name} {ctx.subcommand_name or ''}",
                             icon_url=member.avatar_url)
            await channel.send(embed=embed)

        return wrapper
