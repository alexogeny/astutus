import discord
from typing import List
from discord.ext import commands as cmd


async def can_execute(ctx, member: discord.Member):
    can_execute = (
        ctx.author.id == ctx.bot.owner_id
        or ctx.author == ctx.guild.owner
        or ctx.author.top_role > member.top_role
    )
    if not can_execute:
        raise cmd.BadArgument(
            "You cannot do this due to the user being of same or greater permission than you."
        )


async def executable(ctx, member):
    if not ctx.author.top_role > member.top_role:
        raise cmd.MissingPermissions(["You must be higher in the rolelist"])
    if not ctx.guild.me.top_role > member.top_role:
        raise cmd.MissingPermissions(["The bot must be higher in the role list"])


async def user_has_role(user_roles: List[int], *roles):
    return bool(next((role for role in roles if role in user_roles), None))


# def has_clan_roles(*roles):
#     async def _has_clan_roles(ctx):

#     return cmd.check(_has_clan_roles)


async def user_has_admin_perms(user: discord.Member, guild: discord.Guild):
    return guild.get_member(user.id).guild_permissions.administrator


async def user_has_mod_perms(user: discord.Member, guild: discord.Guild):
    return guild.get_member(user.id).guild_permissions.manage_guild


async def user_has_any_role(user: discord.Member):
    return len(user.roles) > 1


async def check_permissions(ctx: cmd.Context, permissions: dict, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True
    resolved = ctx.channel.permissions_for(ctx.author)
    return check(
        getattr(resolved, name, None) == value for name, value in permissions.items()
    )


async def check_guild_permissions(ctx: cmd.Context, permissions: dict, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True
    if ctx.guild is None:
        return False
    resolved = ctx.author.guild_permissions
    result = check(
        getattr(resolved, name, None) == value for name, value in permissions.items()
    )
    if result:
        return result
    else:
        await ctx.send(
            f"Sorry **{ctx.author}**, you do not have sufficient permissions to use this command."
        )


async def has_permissions(*, check=all, **perms):
    async def predicate(ctx: cmd.Context):
        return await check_permissions(ctx, perms, check=check)

    return cmd.check(predicate)


def is_bot_owner():
    async def predicate(ctx: cmd.Context):
        return str(ctx.author.id) == ctx.bot.config["DEFAULT"]["owner"]

    return cmd.check(predicate)


def is_mod():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"ban_members": True})

    return cmd.check(predicate)


def bot_has_perms(**perms):
    async def predicate(ctx):
        missing = [p for p in perms if not getattr(ctx.guild.me.guild_permissions, p)]
        if missing:
            missing = [perm.replace("_", " ").title() for perm in missing]
            raise cmd.BotMissingPermissions(missing)
        return True

    return cmd.check(predicate)


async def check_for_premium_user(ctx):
    lxmcord = ctx.bot.get_guild(440785686438871040)
    booster = lxmcord.get_role(585600912559439874)
    patreon = lxmcord.get_role(476524707563307008)
    member = lxmcord.get_member(ctx.author.id)
    if not member:
        return False
    if not [x for x in [patreon, booster] if x in member.roles]:
        return False
    return True


def is_premium_user():
    async def predicate(ctx: cmd.Context):
        is_premium = await check_for_premium_user(ctx)
        msg = "Sorry, you are not a premium user. You can become one at <https://patreon.com/lxmcneill> or boost the server with Nitro: https://discord.gg/WvcryZW"
        if not is_premium:
            raise cmd.BadArgument(msg)
        return True

    return cmd.check(predicate)


def is_premium_server():
    async def predicate(ctx):
        prem = await ctx.bot.db.hget("premium", ctx.guild.id)
        if prem is None:
            raise cmd.BadArgument(
                "Not a premium server. Make it one at <https://patreon.com/{}>".format(
                    ctx.bot.config["DEFAULT"]["patreon"]
                )
            )
        return prem is not None

    return cmd.check(predicate)


def can_kick():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"kick_members": True})

    return cmd.check(predicate)


def can_ban():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"ban_members": True})

    return cmd.check(predicate)


def can_manage_nicknames():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"manage_nicknames": True})

    return cmd.check(predicate)


def can_manage_emojis():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"manage_emojis": True})

    return cmd.check(predicate)


def can_manage_roles():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"manage_roles": True})

    return cmd.check(predicate)


def can_manage_channels():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"manage_channels": True})

    return cmd.check(predicate)


def can_create_instant_invite():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"create_instant_invite": True})

    return cmd.check(predicate)


def can_manage_messages():
    async def predicate(ctx: cmd.Context):
        return await check_permissions(ctx, {"manage_messages": True})

    return cmd.check(predicate)


def is_admin():
    async def predicate(ctx: cmd.Context):
        return await check_guild_permissions(ctx, {"administrator": True})

    return cmd.check(predicate)
