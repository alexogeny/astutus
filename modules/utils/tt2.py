import difflib
from math import floor, log10
from discord.ext import commands as cmd
from .checks import can_manage_channels, can_manage_roles
from .etc import snake, get_closest_match


class TTRaidCard(cmd.Converter):
    async def convert(self, ctx: cmd.Context, arg):
        arg = snake(arg)
        cards = ctx.bot.get_cog("TapTitansModule").cards
        return await get_closest_match(arg, cards)


class TTArtifact(cmd.Converter):
    async def convert(self, ctx: cmd.Context, arg):
        arg = snake(arg)
        arts = ctx.bot.get_cog("TapTitansModule").arts
        return await get_closest_match(arg, arts)


class TTSkill(cmd.Converter):
    async def convert(self, ctx: cmd.Context, arg):
        arg = snake(arg)
        skills = ctx.bot.get_cog("TapTitansModule").skills
        return await get_closest_match(arg, skills)


class TTKey(cmd.Converter):
    async def convert(self, ctx: cmd.Context, arg):
        if arg.lower() not in [
            "grandmaster",
            "gm",
            "master",
            "captain",
            "knight",
            "recruit",
            "guest",
            "applicant",
            "timer",
            "tier",
            "zone",
            "average",
            "avg",
            "announce",
            "farm",
            "mode",
            "code",
            "name",
        ]:
            raise cmd.BadArgument(f"**{arg}** not a valid setting for TT2.")
        if arg == "average":
            arg == "avg"
        elif arg == "grandmaster":
            arg == "gm"
        if (
            arg in "gmmastercaptainknightrecruitapplicantguesttimer"
            and not can_manage_roles()
        ):
            raise cmd.BadArgument("You need the manage role permission.")
        if arg == "announce" and not can_manage_channels():
            raise cmd.BadArgument("You need the manage channel permission.")

        return arg.lower()


class TTRaidGroup(cmd.Converter):
    async def convert(self, ctx, arg):
        if arg[0] != "g" or arg[1] not in ("1", "2", "3"):
            raise cmd.BadArgument("Invalid raid group.")
        if arg == "gm":
            raise cmd.BadArgument("Bad?")
        return f"{ctx.guild.id}:tt:{arg[1]}"


async def artifact_boost(level, effect, expo, bos=False):
    return (
        1 + (10 * effect * pow(level, expo))
        if not bos
        else 1 + (effect * pow(level, expo))
    )


async def base_relics_amount(stage: int) -> int:
    return (
        (3 * pow(1.21, pow(stage, 0.48)))
        + (1.5 * (stage - 110))
        + (
            pow(
                1.002,
                pow(stage, min((1.005 * (pow(stage, 1.1 * 0.0000005 + 1))), 1.0155)),
            )
        )
    )


async def primary_craft_boost(level: int) -> float:
    return pow(1.02, level - 1)


async def secondary_craft_boost(level: int) -> float:
    return pow(1.1, level - 1)


async def bonus_relics_amount(stage, bos, sets, craftpower) -> int:
    return await round_to_x(
        await base_relics_amount(stage)
        * await artifact_boost(bos, 0.05, 2.5, 0.0001, 0.12, 0.5)
        * pow(1.5 * await primary_craft_boost(craftpower), max(sets, 0)),
        3,
    )


async def round_to_x(x, n):
    return round(x, -int(floor(log10(x))) + (n - 1))
