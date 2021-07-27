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
                           f"SELECT slash.id, {ctx.guild.id} "
                           f"FROM slash "
                           f"WHERE slash.name = '{cmd}'")

        self.bot.slash.commands[cmd].allowed_guild_ids += ctx.guild.id
        for subcmd in self.bot.slash.subcommands[cmd]:
            subcmd.allowed_guild_ids += ctx.guild.id

        await ctx.message.delete()

    @commands.command()
    @commands.is_owner()
    async def disable_cmd(self, ctx, cmd):
        with DatabaseConnection() as db:
            db.cur.execute(f"DELETE sg FROM slash_guilds sg "
                           f"INNER JOIN slash s ON sg.slash_id = s.id "
                           f"AND s.name = '{cmd}'")

        self.bot.slash.commands[cmd].allowed_guild_ids.remove(ctx.guild.id)
        for subcmd in self.bot.slash.subcommands[cmd]:
            subcmd.allowed_guild_ids.remove(ctx.guild.id)

        await ctx.message.delete()
