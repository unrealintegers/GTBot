def check_owner(ctx):
    return ctx.message.author.id == 330509305663193091


def check_channel(channels):
    if type(channels) is not list:
        channels = [channels]

    def check(ctx):
        return ctx.message.channel.id in channels or check_owner(ctx)

    return check


def check_user(users):
    if type(users) is not list:
        users = [users]

    def check(ctx):
        return ctx.message.author.id in users or check_owner(ctx)

    return check


def check_role(roles):
    if type(roles) is not list:
        roles = [roles]

    def check(ctx):
        return set(roles) & set([x.id for x in ctx.message.author.roles]) or \
               check_owner(ctx)

    return check


def check_category(categories):
    if type(categories) is not list:
        categories = [categories]

    def check(ctx):
        return ctx.message.channel.category.id in categories or \
               check_owner(ctx)

    return check


def check_guild(guilds):
    if type(guilds) is not list:
        guilds = [guilds]

    def check(ctx):
        return ctx.message.channel.guild.id in guilds or check_owner(ctx)

    return check


def check_channel_name_contains(name):
    def check(ctx):
        return name in ctx.message.channel.name or check_owner(ctx)

    return check
