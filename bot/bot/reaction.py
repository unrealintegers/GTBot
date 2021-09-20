from __future__ import annotations

import typing

from discord.ext import commands

if typing.TYPE_CHECKING:
    from .bot import DiscordBot


class ReactionListener(commands.Cog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        self.bot.bot.add_cog(self)

    async def handle_role(self, reaction, role):
        event_type = reaction.event_type
        guild = self.bot.bot.get_guild(reaction.guild_id)
        member = guild.get_member(reaction.user_id)
        role = guild.get_role(role)
        if role in member.roles and event_type == 'REACTION_REMOVE':
            await member.remove_roles(role, reason='Reaction')
        elif event_type == 'REACTION_ADD':
            await member.add_roles(role, reason='Reaction')

    async def handle_reaction(self, reaction):
        if reaction.message_id == 827542930327207936:
            if reaction.emoji.id == 826799810400354325:  # Co-op
                await self.handle_role(reaction, 825302127281700885)
            elif reaction.emoji.id == 828484160750354432:  # Quizzer
                await self.handle_role(reaction, 827538543144468491)
            elif reaction.emoji.id == 828562383378448384:  # EPIC Grinder
                await self.handle_role(reaction, 827538975203262504)
        elif reaction.message_id == 854374759834976306:
            if reaction.emoji.name == '📰':  # Updates
                await self.handle_role(reaction, 852729970525732885)
            elif reaction.emoji.name == '⏰':  # Reminders
                await self.handle_role(reaction, 852730229448769536)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        await self.handle_reaction(reaction)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction):
        await self.handle_reaction(reaction)
