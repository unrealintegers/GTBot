import io
from discord import File
from discord.ext import commands
from discord_slash import SlashContext
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option

from .utils import convert_args


class Evaluate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.result = None

        self.bot.bot.add_cog(self)

    @cog_ext.cog_slash(
        name="eval",
        description="evaluate",
        options=[
            create_option(
                name='command',
                description='What you want to do',
                option_type=str,
                required=False
            ),
        ]
    )
    async def _eval(self, ctx: SlashContext, command: str):
        if ctx.author.id not in [330509305663193091, 475440146221760512]:
            await ctx.send("What do you think you're doing?", hidden=True)
            return

        hidden = (command[0] == "&")
        if hidden:
            command = command[1:]

        if command[0] == command[-1] == '`':
            command = command[1:-1]

        if command.startswith("await "):
            command = command[6:]
            self.result = str(await eval(command))
        else:
            self.result = str(eval(command))

        if len(self.result) > 2000:
            fp = io.BytesIO(self.result.encode('utf-8'))
            await ctx.send(File(fp, "output.txt"))
        else:
            await ctx.send(self.result, hidden=hidden)


class PurgeFlags:
    def __init__(self):
        self.roles = None
        self.members = None
        self.limit = None
        self.reversed = None

    @staticmethod
    async def from_str(ctx, str_):
        purgeflags = PurgeFlags()
        flags = str_.split()

        role_converter = commands.RoleConverter()
        member_converter = commands.MemberConverter()
        args = convert_args(flags)

        if 'r' in args:
            purgeflags.roles = []
            for roles in args['r']:
                for rolestr in roles:
                    role = await role_converter.convert(ctx, rolestr)
                    purgeflags.roles.append(role)
        elif 'a' in args:
            purgeflags.members = []
            for authors in args['a']:
                for authstr in authors:
                    auth = await member_converter.convert(ctx, authstr)
                    purgeflags.members.append(auth)
        if 'l' in args:
            purgeflags.limit = int(args['l'][0][0])

        purgeflags.reversed = 'e' in args

        return purgeflags

    def check(self, msg):
        if self.roles is not None:
            if not set(self.roles).issubset(set(msg.author.roles)):
                return False
        if self.members is not None:
            if msg.author not in self.members:
                return False
        if self.limit is not None:
            if self.limit <= 0:
                return False
            else:
                self.limit -= 1
        return True


class PurgeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.bot.add_cog(self)

    @cog_ext.cog_slash(name="purge",
                       description="Mass deletes messages",
                       options=[
                           create_option("number",
                                         "number of messages to check",
                                         int, True),
                           create_option("flags",
                                         "flags to use: r=role, a=author, "
                                         "e=reverse, l=limit", str, False)
                       ]
                       )
    async def purge(self, ctx: SlashContext, number, flags=''):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM.")
            return

        if not ctx.channel.permissions_for(ctx.author).manage_messages:
            await ctx.send("You need `Manage Messages` to use this command!")
            return

        await ctx.defer(hidden=True)
        flags = await PurgeFlags.from_str(ctx, flags)

        await ctx.channel.purge(limit=number, check=flags.check,
                                oldest_first=flags.reversed)
        await ctx.send("Done!", hidden=True)
