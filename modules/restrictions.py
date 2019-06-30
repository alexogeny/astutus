"""Restrictions module."""

from typing import Union, Optional
from itertools import chain
import discord
from discord.ext import commands as cmd
from discord.utils import find, get
from .utils import checks


class RestrictionsModule(cmd.Cog):
    (
        "Restrict commands! By user, role, and channel.\n"
        "Restrictions a positive match only - meaning you "
        "must meet the restriction criteria to use the command.\n"
    )

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    async def find_command(self, command):
        return self.bot.get_command(" ".join(command))
        # done = 0
        # found = find(
        #     lambda cmx: cmx.name == command[0] or command[0] in cmx.aliases,
        #     self.bot.walk_commands(),
        # )
        # if not found:
        #     raise cmd.BadArgument(
        #         f"Couldn't find any command starting with {command[0]}"
        #     )
        # done += 1
        # while done < len(command):
        #     found = find(
        #         lambda cmx: (cmx.name == command[done] or command[done] in cmx.aliases)
        #         and cmx.parent == found,
        #         self.bot.walk_commands(),
        #     )
        #     if not found:
        #         raise cmd.BadArgument(
        #             f"Couldn't find any command starting with {command[done]}"
        #         )
        #     done += 1
        # return found

    async def get_restrictions(self, guild, command):
        r_chan = await self.bot.db.lrange(f"{guild.id}:rst:c:{command}")
        r_role = await self.bot.db.lrange(f"{guild.id}:rst:r:{command}")
        r_memb = await self.bot.db.lrange(f"{guild.id}:rst:m:{command}")
        items = list(chain.from_iterable((r_chan or [], r_role or [], r_memb or [])))
        return items, r_chan, r_role, r_memb

    @cmd.group(name="restrictions", aliases=["restrict"], invoke_without_command=True)
    async def restrictions(self, ctx, *command):
        if cmd is None:
            return
        found = await self.find_command(command)
        restrictions, chans, roles, membs = await self.get_restrictions(
            ctx.guild, found
        )
        if not restrictions:
            raise cmd.BadArgument(f"**{found}** is not currently restricted.")
        chans = [get(ctx.guild.channels, id=int(c)) for c in chans]
        roles = [get(ctx.guild.roles, id=int(c)) for c in roles]
        membs = [get(ctx.guild.members, id=int(c)) for c in membs]
        rolmem = list(chain.from_iterable((roles, membs)))
        text = "**{}** can only be used".format(found)
        if chans:
            text = text + " in " + ", ".join([f"**#{x}**" for x in chans])
        if rolmem:
            text = text + " by " + ", ".join([f"**@{x}**" for x in rolmem])

        await ctx.send(text + ".")

    @checks.is_mod()
    @restrictions.command(name="mode")
    async def restrictions_mode(self, ctx, mode: Optional[str] = None):
        if mode is None:
            mode = await self.bot.db.hget(f"{ctx.guild.id}:set", "rmode")
            await ctx.send(
                "Restriction mode for {} is set to: {}".format(
                    ctx.guild, mode is None and "or" or mode
                )
            )
            return
        if mode.lower() not in ["and", "or"]:
            raise cmd.BadArgument(
                "Restriction mode must be one of: {}".format(
                    ", ".join([f"**{x}**" for x in ["and", "or"]])
                )
            )
        await self.bot.db.hset(f"{ctx.guild.id}:set", "rmode", mode.lower())
        await ctx.send(
            ":white_check_mark: Set restriction mode to: **{}**".format(mode.lower())
        )

    @checks.is_mod()
    @restrictions.command(name="add")
    async def restrictions_add(
        self,
        ctx,
        command,
        *objects: Union[
            cmd.TextChannelConverter, cmd.RoleConverter, cmd.MemberConverter
        ],
    ):
        if command.startswith("restrict"):
            raise cmd.BadArgument("You cannot restrict the restrictions command.")
        command = command.split()
        found = await self.find_command(command)
        items, chan, role, mem = await self.get_restrictions(ctx.guild, found)
        to_add = [x for x in objects if str(x.id) not in items]
        if len(items) == 10 or len(items) + len(to_add) > 10:
            raise cmd.BadArgument(
                "No more than **10** restrictions per command are allowed."
            )
        for add_x in to_add:
            if isinstance(add_x, discord.TextChannel):
                await self.bot.db.rpush(f"{ctx.guild.id}:rst:c:{found}", add_x.id)
            elif isinstance(add_x, discord.Role):
                await self.bot.db.rpush(f"{ctx.guild.id}:rst:r:{found}", add_x.id)
            elif isinstance(add_x, discord.Member):
                await self.bot.db.rpush(f"{ctx.guild.id}:rst:m:{found}", add_x.id)

        await ctx.send(
            ":{}_mark: Added **{}** item{} to **{}** restrictions.".format(
                len(to_add) and "white_check" or "negative_squared_cross",
                len(to_add),
                len(to_add) != 1 and "s" or "",
                found,
            )
        )

    @checks.is_mod()
    @restrictions.command(name="remove", aliases=["rem", "del", "delete"])
    async def restrictions_remove(
        self,
        ctx,
        command,
        *objects: Union[
            cmd.TextChannelConverter, cmd.RoleConverter, cmd.MemberConverter
        ],
    ):
        if command.startswith("restrict"):
            raise cmd.BadArgument("You cannot restrict the restrictions command.")
        command = command.split()
        found = await self.find_command(command)
        items, chan, role, mem = await self.get_restrictions(ctx.guild, found)
        to_del = [x for x in objects if str(x.id) in items]

        for add_x in to_del:
            if str(add_x.id) in chan:
                await self.bot.db.lrem(f"{ctx.guild.id}:rst:c:{found}", add_x.id)
            elif str(add_x.id) in role:
                await self.bot.db.lrem(f"{ctx.guild.id}:rst:r:{found}", add_x.id)
            elif str(add_x.id) in mem:
                await self.bot.db.lrem(f"{ctx.guild.id}:rst:m:{found}", add_x.id)

        await ctx.send(
            ":{}_mark: Removed **{}** item{} from **{}** restrictions.".format(
                len(to_del) and "white_check" or "negative_squared_cross",
                len(to_del),
                len(to_del) != 1 and "s" or "",
                found,
            )
        )

    @checks.is_mod()
    @restrictions.command(name="erase", aliases=["wipe", "clear"])
    async def restrictions_erase(self, ctx, command):
        if command.startswith("restrict"):
            raise cmd.BadArgument("You cannot restrict the restrictions command.")
        command = command.split()
        found = await self.find_command(command)
        items, chan, role, mem = await self.get_restrictions(ctx.guild, found)
        count = len(items)
        if chan:
            await self.bot.db.delete(f"{ctx.guild.id}:rst:c:{found}")
        if role:
            await self.bot.db.delete(f"{ctx.guild.id}:rst:r:{found}")
        if mem:
            await self.bot.db.delete(f"{ctx.guild.id}:rst:m:{found}")

        await ctx.send(
            ":{}_mark: Removed **{}** item{} from **{}** restrictions.".format(
                count and "white_check" or "negative_squared_cross",
                count,
                count != 1 and "s" or "",
                found,
            )
        )


def setup(bot):
    """Bind the module to the bot."""
    bot.add_cog(RestrictionsModule(bot))
