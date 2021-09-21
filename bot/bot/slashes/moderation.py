import io

from discord import File
from discord.app import ApplicationContext, Option
from discord.ext.commands import RoleConverter, MemberConverter

from ..bot import DiscordBot, SlashCommand
from ..utils import convert_args


class Evaluate(SlashCommand, name="evaluate"):
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        super().__init__(bot, guild_ids)

        self.result = None

        self.register(self._eval, name="eval")

    async def _eval(
            self, ctx: ApplicationContext,
            command: Option(str, "&h")
    ):
        if ctx.user.id not in [330509305663193091, 475440146221760512]:
            await ctx.respond("What do you think you're doing?",
                              ephemeral=True)
            return
        """evaluate"""
        ephemeral = (command[0] == "&")
        if ephemeral:
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
            await ctx.respond(file=File(fp, "output.txt"))
        else:
            await ctx.respond(self.result, ephemeral=ephemeral)


class PurgeFlags:
    def __init__(self):
        self.roles = None
        self.members = None
        self.limit = None
        self.reversed = None
        self.count = 0

    @staticmethod
    async def from_str(ctx, str_):
        purgeflags = PurgeFlags()
        flags = str_.split()

        role_converter = RoleConverter()
        member_converter = MemberConverter()
        args = convert_args(flags)

        if 'r' in args:
            purgeflags.roles = []
            for roles in args['r']:
                for rolestr in roles.split():
                    role = await role_converter.convert(ctx, rolestr)
                    purgeflags.roles.append(role)
        elif 'a' in args:
            purgeflags.members = []
            for authors in args['a']:
                for authstr in authors.split():
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
        self.count += 1
        return True


class PurgeCommand(SlashCommand, name="purge"):
    def __init__(self, bot: DiscordBot, guild_ids: list[int]):
        super().__init__(bot, guild_ids)

        self.register(self.purge)

    async def purge(
            self, ctx: ApplicationContext,
            number: Option(int, "number of messages"),
            flags: Option(str, "purge flags", required=False) = ''
    ):
        """Mass delete messages"""
        if ctx.guild is None:
            await ctx.respond("This command cannot be used in a DM.")
            return

        if not ctx.channel.permissions_for(ctx.author).manage_messages:
            await ctx.respond("You need `Manage Messages` to "
                              "use this command!", ephemeral=True)
            return

        perm = ctx.channel.permissions_for(ctx.guild.me)
        if not perm.administrator and not perm.manage_messages:
            await ctx.respond("I do not have the `Manage Messages` permission "
                              "in this channel!", ephemeral=True)

        await ctx.defer(ephemeral=True)
        flags = await PurgeFlags.from_str(ctx, flags)

        await ctx.channel.purge(limit=number, check=flags.check,
                                oldest_first=flags.reversed)
        await ctx.respond(f"{flags.count} messages deleted!", ephemeral=True)
