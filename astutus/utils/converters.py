from discord.ext import commands as cmd
import discord


class Truthy(cmd.Converter):
    async def convert(self, ctx, argument):
        arg = argument.lower()
        if arg not in [
            "0",
            "1",
            "2",
            "strong",
            "weak",
            "on",
            "off",
            "true",
            "false",
            "yes",
            "no",
        ]:
            raise cmd.BadArgument()
        elif arg in ["on", "true", "1", "yes", "weak"]:
            return 1
        elif arg in ["2", "strong"]:
            return 2
        return 0


class ChannelID(cmd.Converter):
    async def convert(self, ctx: cmd.Context, argument):
        try:
            c = await cmd.TextChannelConverter().convert(ctx, argument)
        except cmd.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                try:
                    c = next(
                        (
                            c
                            for c in ctx.guild.text_channels
                            if any(
                                (
                                    c.name.lower() == argument.lower(),
                                    argument.lower() in c.name.lower(),
                                )
                            )
                        ),
                        None,
                    )
                except:
                    pass
                if not c:
                    raise cmd.BadArgument(
                        f"Sorry, the phrase **{argument}** did not return any channels."
                    )

        return c.id


class MemberID(cmd.Converter):
    async def convert(self, ctx: cmd.Context, argument):
        try:
            m = await cmd.MemberConverter().convert(ctx, argument)
        except cmd.BadArgument:
            try:
                return int(argument, base=10)
            except:
                raise cmd.BadArgument(
                    f"Sorry, the phrase **{argument}** did not return any members."
                )
        return m.id


class ActionReason(cmd.Converter):
    async def convert(self, ctx: cmd.Context, argument):
        if argument is not None:
            result = f"{ctx.author.id}_:_{argument}"
        elif len(result) > 140:
            result = f"{ctx.author.id}_:_{argument[0:137]}..."
        elif argument is None or argument == "":
            result = f"{ctx.author.id}_:_"
        return result


class BannedMember(cmd.Converter):
    async def convert(self, ctx: cmd.Context, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)
            entity = discord.utils.find(lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            await ctx.send(f"Not a previously banned member.")
            raise cmd.BadArgument("Not a valid previously-banned member.")
        return entity
