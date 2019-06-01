from discord.ext import commands as cmd
from discord.ext import tasks as tsk
from astutus.utils import Delta
from typing import Optional
import asyncpg


class TapTitans(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.timers = []
        self.raid_timer.add_exception_type(asyncpg.PostgresConnectionError)
        self.raid_timer.start()

    @tsk.loop(minutes=1.0)
    async def raid_timer(self):
        print("check timers")

    @cmd.group(case_insensitive=True)
    async def tt(self):
        return

    @tt.group(name="raid", aliases=["boss", "rd"], case_insensitive=True)
    async def tt_raid(self):
        return

    @tt_raid.command(name="start", aliases=["prep"])
    async def raid_start(self, ctx: cmd.Context, level: str, time: Optional[Delta]):
        # get levels from user or clan in db
        # set spawn to 24h from now or the <time> argument
        # add the timer to the internal list and to the db
        # return a statement of confirmation
        return

    @tt_raid.command(name="clear", aliases=["end", "failed", "ended", "cleared"])
    async def raid_clear(self):
        return

    @tt_raid.command(name="info", aliases=["information"])
    async def raid_info(self):
        return

    @tt.group(name="queue", aliases=["q"], case_insensitive=True)
    async def tt_queue(self, cancel: bool = True):
        return

    @tt.group(name="card", case_insensitive=True)
    async def tt_card(self):
        return

    @tt.group(name="deck", case_insensitive=True)
    async def tt_deck(self):
        return

    @tt.group(name="hero", case_insensitive=True)
    async def tt_hero(self):
        return

    @tt.group(name="equip", case_insensitive=True)
    async def tt_equip(self):
        return

    @tt.group(name="artifact", case_insensitive=True)
    async def tt_artifact(self):
        return

    @tt.group(name="set", case_insensitive=True)
    async def tt_set(self):
        return

    @tt.group(name="enhancement", case_insensitive=True)
    async def tt_enhance(self):
        return

    @tt.group(name="enchant", case_insensitive=True)
    async def tt_enchant(self):
        return

    @tt.group(name="titan", case_insensitive=True)
    async def tt_titan(self):
        return

    @tt.group(name="titanlord", case_insensitive=True)
    async def tt_titanlord(self):
        return

    @tt.group(name="skill", case_insensitive=True)
    async def tt_skill(self):
        return
