import asyncio
import arrow
import discord
from discord.ext import commands as cmd


async def search_for(items, term):
    results = list({x for x in items if term.lower() in str(x).lower()})
    return [(results.index(r) + 1, r) for r in results]


async def choose_from(ctx, choices, text, embed, timeout=30):
    chooser = await ctx.send(text, embed=embed)

    def check(message):
        return (
            message.author == ctx.author
            and message.channel == ctx.channel
            and message.content.lower()
            in list(map(lambda c: str(c[0]), choices)) + ["c"]
        )

    try:
        msg = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        await chooser.delete()
        raise cmd.BadArgument("Query timed out.")

    await chooser.delete()

    if msg.content.lower() == "c":
        raise cmd.BadArgument("Query cancelled by user.")

    i = int(msg.content) - 1
    return choices[i]


async def choose_item(ctx, kind, guild, query: str):
    kind2 = kind.replace("_", " ").title().replace(" ", "")
    try:
        test = await getattr(cmd, f"{kind2}Converter")().convert(ctx, query)
        if test is not None:
            return test
    except cmd.BadArgument:
        pass

    result = await search_for(getattr(guild, f"{kind}s"), query)
    if len(result) == 1:
        _, yes = result[0]
        return yes
    if not result:
        raise cmd.BadArgument("No {} found.".format(kind.replace("_", " ")))
    choices = result[0:20]
    text = f"Please choose a number from the following:"
    embed = await ctx.bot.embed()
    embed.description = "\n".join([f"{x}. {y}" for x, y in choices])
    _, choice = await choose_from(ctx, choices, text, embed, timeout=60.0)
    return choice
