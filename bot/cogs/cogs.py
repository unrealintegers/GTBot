from discord.ext import commands

from .utils import DatabaseConnection


class CogCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def enable_cmd(self, ctx, cmd):
        with DatabaseConnection() as db:
            db.cur.execute(f"INSERT INTO slash_guilds (slash_id, guild_id) "
                           f"SELECT s.id, {ctx.guild.id} "
                           f"FROM slashes AS s "
                           f"WHERE s.name = '{cmd}'")

        if ctx.guild.id not in self.bot.slash.commands[cmd].allowed_guild_ids:
            self.bot.slash.commands[cmd].allowed_guild_ids.append(ctx.guild.id)
        for subcmd in self.bot.slash.subcommands[cmd].values():
            if ctx.guild.id not in subcmd.allowed_guild_ids:
                subcmd.allowed_guild_ids.append(ctx.guild.id)

        await self.bot.slash.sync_all_commands()
        await ctx.message.delete()

    @commands.command()
    @commands.is_owner()
    async def disable_cmd(self, ctx, cmd):
        with DatabaseConnection() as db:
            db.cur.execute(f"DELETE FROM slash_guilds AS sg "
                           f"USING slashes AS s WHERE s.id = sg.slash_id "
                           f"AND s.name = '{cmd}'")

        if ctx.guild.id in self.bot.slash.commands[cmd].allowed_guild_ids:
            self.bot.slash.commands[cmd].allowed_guild_ids.remove(ctx.guild.id)
        for subcmd in self.bot.slash.subcommands[cmd].values():
            if ctx.guild.id in subcmd.allowed_guild_ids:
                subcmd.allowed_guild_ids.remove(ctx.guild.id)

        await self.bot.slash.sync_all_commands()
        await ctx.message.delete()
