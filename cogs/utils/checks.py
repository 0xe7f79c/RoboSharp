from discord.ext import commands

from bot import DEBUG, GuildContext

PSINI_USER_ID = 593294576026910720

if not DEBUG:
    LANCE_USER_ID = 514542702013186049
else:
    LANCE_USER_ID = PSINI_USER_ID


def lance_only():
    async def wrapper(ctx: GuildContext) -> bool:
        if ctx.guild is None:
            return False
        elif ctx.author.id != LANCE_USER_ID:
            await ctx.reply('This command can only be run by lance.')
            return False

        permissions = ctx.channel.permissions_for(ctx.author)
        if not permissions.administrator:
            await ctx.reply('\N{NO ENTRY} LanceUtils is blocked if Lance isnt Admin.')
            return False

        return True

    return commands.check(wrapper)


def bunker_only():
    async def wrapper(ctx: GuildContext) -> bool:
        if ctx.guild is None:
            return False

        if ctx.guild.id != int(ctx.config.bunker_guild_id):
            await ctx.reply('\N{NO ENTRY SIGN} This is a restricted command.')
            return False

        ctx.bunker_id = ctx.config.bunker_guild_id
        return True

    return commands.check(wrapper)
