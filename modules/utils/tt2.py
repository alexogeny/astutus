import difflib
from decimal import Decimal
from math import floor, log10
from itertools import chain
from discord.ext import commands as cmd
from .checks import can_manage_channels, can_manage_roles
from .etc import snake, get_closest_match

TREE_MAP = dict(Red=0, Yellow=1, Blue=2, Green=3)
# TALENT_MAP = {
#     "HelperBoost": lambda a, b, c, d, e: pow(((1 + b) / (1 + a)), (e / (d - c))),
#     "HelperInspiredWeaken": lambda a, b, c, d, e: pow(
#         ((1 + 0.5 * b) / (1 + 0.5 * a)), (e / (d - c))
#     ),
#     "CritSkillBoost": lambda a, b, c, d, e: pow(((1 + b) / (1 + a)), (e / (d - c))),
# }
PCT_BOOSTS = dict(HelperBoost=1, CritSkillBoost=1, HelperInspiredWeaken=1)
TALENT_SWAP = dict(PetOfflineDmg="B", InactiveClanShip="B", OfflineCloneDmg="B")


async def get_total_sp_spent(tree, skills):
    data = dict(BranchRed=0, BranchYellow=0, BranchBlue=0, BranchGreen=0)
    for t in tree:
        for skill in tree[t]:
            skx = next((s for s in skills if s["TalentID"] == skill), None)
            total = sum([int(skx[f"C{x}"]) for x in range(0, tree[t][skill])])
            data[t] += total
    return data


def get_reduced_effect(effect1, effect2, cost1, cost2, reduction):
    return pow((effect2 / effect1), (reduction / (cost2 - cost1)))


def process_skills_to_opti(skills, damage_reductions, gold_reductions):
    result = {}
    for i, skill in enumerate(skills):
        skx = dict(
            id=i,
            max=int(skill["MaxLevel"]),
            tier=skill["Tier"],
            costs=[],
            effects=[],
            efficiencies=dict(damage={}, gold={}),
            reductions=dict(damage={}, gold={}),
            spreq=int(skill["SPReq"]),
            slot=int(skill["Slot"]),
            talentreq=skill["TalentReq"],
            ignored=[],
            branch=skill["Branch"],
            name=skill["TalentID"],
        )
        # id = int(skill["Slot"]) + TREE_MAP[skill["Branch"][6:]] * 9
        id = i
        for dmg, arr in damage_reductions.items():
            if arr[id] != 0 and "gold" not in skill["Note"].lower():
                skx["reductions"]["damage"][dmg] = arr[id]
                skx["efficiencies"]["damage"][dmg] = []
        for gold, arr in gold_reductions.items():
            if arr[id] != 0 and "gold" in skill["Note"].lower():
                skx["reductions"]["gold"][gold] = arr[id]
                skx["efficiencies"]["gold"][gold] = []

        for field, val in skill.items():
            if field.startswith("C") and val.isdigit():
                skx["costs"].append(int(val))
            elif field.startswith("A") and field[1:].isdigit():
                if val not in ["-", "0"]:
                    swap = TALENT_SWAP.get(skill["TalentID"], "A")
                    effect2 = float(
                        Decimal(skill[swap + field[1:]])
                        + PCT_BOOSTS.get(skill["TalentID"], 0)
                    )
                    skx["effects"].append(effect2)
                    idx = max(len(skx["effects"]), 1)
                    cost1 = sum(skx["costs"][: idx - 1]) or 0
                    cost2 = sum(skx["costs"][:idx])
                    if cost1 == cost2 or int(field[1:]) == 1:
                        effect1 = 1
                        cost1 = 0
                    else:
                        effect1 = skx["effects"][idx - 2]

                    if "gold" not in skill["Note"].lower():
                        for key, red in skx["reductions"]["damage"].items():
                            if skx["name"] == "HelperDmgQTE":
                                skx["efficiencies"]["damage"][key].append(
                                    5 * pow((effect2 / effect1), red * (cost2 - cost1))
                                )
                            elif skx["name"] not in TALENT_SWAP or cost1 != 0:
                                skx["efficiencies"]["damage"][key].append(
                                    get_reduced_effect(
                                        effect1, effect2, cost1, cost2, red
                                    )
                                )
                            else:
                                skx["efficiencies"]["damage"][key].append(pow(5, cost2))

                    else:
                        for key, red in skx["reductions"]["gold"].items():
                            skx["efficiencies"]["gold"][key].append(
                                get_reduced_effect(
                                    effect1, effect2, cost1, cost2, pow(red, 0.72)
                                )
                            )

        result[skill["TalentID"]] = skx
    return result


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


def is_arg(arg):
    return arg and arg.lower() or ""


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
