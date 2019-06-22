from math import floor, log10


async def artifact_boost(
    level: int,
    per_level: int,
    cost_exponent: float,
    growth_rate,
    growth_max,
    growth_exponent,
) -> int:
    return round(
        1
        + per_level
        * pow(
            level,
            pow(
                (1 + (cost_exponent - 1) * min(growth_rate * level, growth_max)),
                growth_exponent,
            ),
        )
        + 0.5
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
