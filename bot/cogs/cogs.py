from discord.ext import commands


class CogCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def sync_cmds(self):
        cmds = self.bot.db.fetch("SELECT slash_guilds.guild_id, slashes.name "
                                 "FROM slash_guilds INNER JOIN slashes "
                                 "ON slash_guilds.slash_id = slashes.id")
        names = set(map(lambda x: x[1], cmds))
        cmd_dict = {n: set(filter(lambda x: x[1] == n, cmds)) for n in names}

        guild_ids = set([g.id for g in self.bot.bot.guilds])
        for cmd in cmd_dict:
            allowed_ids = list(cmd_dict[cmd] & guild_ids)
            self.bot.slash.commands[cmd].allowed_guild_ids = allowed_ids

            for subcmd in self.bot.slash.subcommands[cmd].values():
                subcmd.allowed_guild_ids = allowed_ids

    @commands.command()
    @commands.is_owner()
    async def enable_cmd(self, ctx, cmd):
        self.bot.db.execute(f"""
            INSERT INTO slash_guilds (slash_id, guild_id) 
            SELECT s.id, {ctx.guild.id} 
            FROM slashes AS s 
            WHERE s.name = '{cmd}'
        """)

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
        self.bot.db.execute(f"""
            DELETE FROM slash_guilds AS sg 
            USING slashes AS s WHERE s.id = sg.slash_id 
            AND s.name = '{cmd}'
        """)

        if ctx.guild.id in self.bot.slash.commands[cmd].allowed_guild_ids:
            self.bot.slash.commands[cmd].allowed_guild_ids.remove(ctx.guild.id)
        for subcmd in self.bot.slash.subcommands[cmd].values():
            if ctx.guild.id in subcmd.allowed_guild_ids:
                subcmd.allowed_guild_ids.remove(ctx.guild.id)

        await self.bot.slash.sync_all_commands()
        await ctx.message.delete()
