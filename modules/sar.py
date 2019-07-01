from discord.ext import commands as cmd
from .utils import checks
from .utils.converters import MemberID, ActionReason, BannedMember, Truthy
import arrow
from math import floor
from datetime import timedelta
from random import random
import arrow
from typing import Optional


class SarModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.postie = None

    @cmd.Cog.listener()
    async def on_ready(self):
        self.postie = self.bot.get_cog("PostgreModule")

    async def get_sars(self, ctx):
        data = await self.postie.sql_query_db(
            f"SELECt * FROM Sar WHERE id = {ctx.guild.id}"
        )
        groups = {}
        if not data or data is None:
            return groups
        data = dict(data)
        for i in [1, 2, 3, 4, 5]:
            group = data.get(f"group{i}_name", None)
            if group is not None:
                roles = data.get(f"group{i}_name", "").split()
                roles_mapped = []
                for role in roles:
                    guild_role = await ctx.guild.fetch_role(int(role))
                    if guild_role is not None:
                        roles_mapped.append(guild_role)
                groups[group] = dict(roles=roles_mapped, id=i)
        return groups

    @cmd.guild_only()
    @checks.is_mod()
    @checks.bot_has_perms(manage_roles=True)
    @cmd.group(name="sar", invoke_without_command=True)
    async def sar(self, ctx):
        return

    @sar.group(name="group", invoke_without_command=True)
    async def sar_group(self, ctx):
        groups = await self.get_sars(ctx)
        if not groups:
            raise cmd.BadArgument(
                "No SAR groups for {}. Add one with {}sar group create <name>".format(
                    ctx.guild, ctx.prefix
                )
            )
        embed = await self.bot.embed()
        embed.title = f'SAR groups for {ctx.guild}'
        for group, vals in groups.items():
            embed.add_field(
                name=f"{vals['id']}. {group}",
                value=', '.join([
                    role.mention for role in vals['roles']
                ])
            )
        await ctx.send(embed=embed)

    @sar_group.command(name="create")
    async def sar_group_create(self, ctx, name, excl: Optional[bool] = True):
        groups = await self.get_sars(ctx)
        if len(groups) > 4:
            raise cmd.BadArgument("5 group SAR limit reached.")
        if name.lower() in [g.lower() for g in groups.keys()]:
            raise cmd.BadArgument(f"SAR group with name {name} already exists.")
        new_group = dict(excl=excl, roles=[])
        groups[name] = new_group

    @sar_group.command(name="delete")
    async def sar_group_delete(self, ctx, name):
        return

    @sar_group.command(name="add")
    async def sar_group_add(self, ctx, group, roles: cmd.Greedy[cmd.RoleConverter]):
        return

    @sar_group.command(name="remove")
    async def sar_group_remove(self, ctx, group, roles: cmd.Greedy[cmd.RoleConverter]):
        return


def setup(bot):
    bot.add_cog(SarModule(bot))
