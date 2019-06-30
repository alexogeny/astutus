import aiohttp
import discord
from discord.ext import commands as cmd
from urllib.parse import quote_plus

NEWTON_API_CALL = "https://newton.now.sh/{}/{}"


class MathModule(cmd.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def newton(self, ctx, operation, *, expression=None):

        # Check if expression is None
        if expression is None:
            raise cmd.BadArgument("You need to specify an expression.")

        expression = quote_plus(expression.replace("/", "(over)").replace(" ", ""))
        async with aiohttp.ClientSession() as client:
            async with client.get(
                NEWTON_API_CALL.format(operation, expression)
            ) as resp:
                res = await resp.json()
        await ctx.send(
            ":1234: Your expression evaluates to `{}`, @**{}**.".format(
                res["result"], ctx.author
            )
        )

    @cmd.cooldown(1, 10, cmd.BucketType.user)
    @cmd.group(
        name="math", invoke_without_command=True, aliases=["=", "==", "= ", "== "]
    )
    async def math(self, ctx, *, expression=None):
        await self.newton(ctx, "simplify", expression=expression)

    @math.command(name="factor")
    async def factor(self, ctx, *, expression=None):
        await self.newton(ctx, "factor", expression=expression)

    @math.command(name="derivative", aliases=["derivate", "derive", "dv"])
    async def derivative(self, ctx, *, expression=None):
        await self.newton(ctx, "derive", expression=expression)

    @math.command(name="integral", aliases=["integrate"])
    async def integral(self, ctx, *, expression=None):
        await self.newton(ctx, "integrate", expression=expression)

    @math.command(name="zeroes", aliases=["zero"])
    async def zeroes(self, ctx, *, expression=None):
        await self.newton(ctx, "zeroes", expression=expression)

    @math.command(name="cosine", aliases=["cos"])
    async def cosine(self, ctx, *, value=None):
        await self.newton(ctx, "cos", expression=value)

    @math.command(name="sine", aliases=["sin"])
    async def sine(self, ctx, *, value=None):
        await self.newton(ctx, "sin", expression=value)

    @math.command(name="tangent", aliases=["tan"])
    async def tangent(self, ctx, *, value=None):
        await self.newton(ctx, "tan", expression=value)

    @math.command(name="arccosine", aliases=["arccos"])
    async def arccosine(self, ctx, *, value=None):
        await self.newton(ctx, "arccos", expression=value)

    @math.command(name="arcsine", aliases=["arcsin"])
    async def arcsine(self, ctx, *, value=None):
        await self.newton(ctx, "arcsin", expression=value)

    @math.command(name="arctangent", aliases=["arctan"])
    async def arctangent(self, ctx, *, value=None):
        await self.newton(ctx, "arctan", expression=value)

    @math.command(name="absolute", aliases=["abs"])
    async def absolute(self, ctx, *, value=None):
        await self.newton(ctx, "abs", expression=value)

    # @math.command(name="tangentLine", aliases=["tanLine"])
    # async def tangent_line(self, ctx, x=None, *, expression=None):

    #     # Check if x is None
    #     if x == None:
    #         await ctx.send(
    #             embed=get_error_message(
    #                 "In order to get the tangent line at a point, you need the x value."
    #             )
    #         )

    #     # Check if expression is None
    #     elif expression == None:
    #         await ctx.send(
    #             embed=get_error_message(
    #                 "In order to get the tangent line at x, you need the expression."
    #             )
    #         )

    #     # Neither are None; Call the API
    #     else:

    #         # Make expression URL-safe and call the API
    #         expression = quote_plus(
    #             "{}|{}".format(x, expression.replace("/", "(over)").replace(" ", ""))
    #         )
    #         response = await database.loop.run_in_executor(
    #             None, requests.get, NEWTON_API_CALL.format("tangent", expression)
    #         )
    #         response = response.json()

    #         # Create embed and send message
    #         await ctx.send(
    #             embed=discord.Embed(
    #                 title="Tangent Line",
    #                 description="Result: `{}`".format(response["result"]),
    #                 colour=await get_embed_color(ctx.author),
    #             )
    #         )

    # @math.command(name="areaUnderCurve", aliases=["areaCurve", "area"])
    # async def area_under_curve(self, ctx, x_start=None, x_end=None, *, expression=None):

    #     # Check if x_start is None
    #     if x_start == None:
    #         await ctx.send(
    #             embed=get_error_message(
    #                 "In order to find the area underneath a curve, you need to specify the starting x point."
    #             )
    #         )

    #     # Check if x_end is None
    #     elif x_start == None:
    #         await ctx.send(
    #             embed=get_error_message(
    #                 "In order to find the area underneath a curve, you need to specify the ending x point."
    #             )
    #         )

    #     # Check if expression is None
    #     elif expression == None:
    #         await ctx.send(
    #             embed=get_error_message(
    #                 "In order to find the area underneath a curve, you need the expression."
    #             )
    #         )

    #     # Nothing is None; Call the API
    #     else:

    #         # Make expression URL-safe and call the API
    #         expression = quote_plus(
    #             "{}:{}|{}".format(
    #                 x_start, x_end, expression.replace("/", "(over)").replace(" ", "")
    #             )
    #         )
    #         response = await database.loop.run_in_executor(
    #             None, requests.get, NEWTON_API_CALL.format("area", expression)
    #         )
    #         response = response.json()

    #         # Create embed and send message
    #         await ctx.send(
    #             embed=discord.Embed(
    #                 title="Area under a curve",
    #                 description="Result: `{}`".format(response["result"]),
    #                 colour=await get_embed_color(ctx.author),
    #             )
    #         )

    # @math.command(name="logarithm", aliases=["log"])
    # async def log(self, ctx, value=None, base: int = 10):

    #     # Check if value is None
    #     if value == None:
    #         await ctx.send(
    #             embed=get_error_message(
    #                 "To get the logarithm of a number, you need to specify the number."
    #             )
    #         )

    #     else:

    #         # Make expression URL-safe and call the API
    #         expression = quote_plus("{}|{}".format(base, value))
    #         response = await database.loop.run_in_executor(
    #             None, requests.get, NEWTON_API_CALL.format("log", expression)
    #         )
    #         response = response.json()

    #         # Create embed and send message
    #         await ctx.send(
    #             embed=discord.Embed(
    #                 title="Logarithm",
    #                 description="Result: `{}`".format(response["result"]),
    #                 colour=await get_embed_color(ctx.author),
    #             )
    #         )


def setup(bot):
    bot.add_cog(MathModule(bot))
