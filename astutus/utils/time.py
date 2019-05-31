from discord.ext import commands as cmd
import re
import arrow


COMPILED = re.compile(
    r"(?:(?P<years>[0-9])(?:years?|y))?"
    r"(?:(?P<months>[0-9])(?:months?|mo))?"
    r"(?:(?P<weeks>[0-9])(?:weeks?|w))?"
    r"(?:(?P<days>[0-9])(?:days?|d))?"
    r"(?:(?P<hours>[0-9])(?:hours?|h))?"
    r"(?:(?P<minutes>[0-9])(?:minutes?|m))?"
    r"(?:(?P<seconds>[0-9])(?:seconds?|s))?"
)


class HumanTimeDelta(cmd.Converter):
    async def convert(self, ctx: cmd.Context, argument):
        match = COMPILED.fullmatch(argument)
        if match is None or not match.group(0):
            match = COMPILED.fullmatch("1y")
            raise cmd.BadArgument('No valid expiry date provided for moderation action.')
        data = {key: int(value) for key, value in match.groupdict(default=0).items()}
        now = arrow.utcnow()
        return now.shift(**data)
