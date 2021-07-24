from discord.ext import commands

from .utils import *

purgereqs = {}


def purgecheck(msg):
    global purgereqs
    if 'roles' in purgereqs:
        if not set(purgereqs['roles']).issubset(set(msg.author.roles)):
            return False
    if 'author' in purgereqs:
        if msg.author not in purgereqs['author']:
            return False
    if 'limit' in purgereqs:
        if purgereqs['limit'] <= 0:
            return False
        else:
            purgereqs['limit'] -= 1
    return True


class PurgeCommand(commands.Cog):
    @commands.command()
    @commands.is_owner()
    async def purge(self, ctx, num, *args):
        global purgereqs
        i = 0
        reverse = False
        opt = convert_args(args)
        if 'r' in opt:
            purgereqs['roles'] = []
            for roles in opt['r']:
                for rolestr in roles:
                    role = await commands.RoleConverter().convert(ctx, rolestr)
                    purgereqs['roles'].append(role)
        elif 'a' in opt:
            purgereqs['author'] = []
            for authors in opt['a']:
                for authstr in authors:
                    auth = await commands.MemberConverter().convert(ctx, authstr)
                    purgereqs['author'].append(auth)
        if 'e' in opt:
            reverse = True
        if 'l' in opt:
            purgereqs['limit'] = int(opt['l'][0][0])
        await ctx.channel.purge(limit=(int(num) + 1), check=purgecheck, oldest_first=reverse)
        purgereqs = {}