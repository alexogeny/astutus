from discord.ext import commands as cmd
from .utils import checks
from .utils.converters import MemberID, ActionReason, BannedMember, Truthy
import arrow
from math import floor
from datetime import timedelta
from random import random
import arrow
import asyncio
from typing import Optional


class SarModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.postie = None

    @cmd.Cog.listener()
    async def on_ready(self):
        setattr(self, "postie", self.bot.get_cog("PostgreModule"))

    async def get_sars(self, ctx):
        data = await self.bot.get_cog("PostgreModule").sql_query_db(
            "SELECT * FROM public.sar WHERE id = {}".format(ctx.guild.id)
        )
        groups = {}
        if not data or data is None:
            return groups
        data = dict(data)
        for i in [1, 2, 3, 4, 5]:
            group = data.get(f"group{i}_name", None)
            if group is not None:
                roles = (data.get(f"group{i}_roles", None) or "").split()
                roles_mapped = []
                for role in roles:
                    guild_role = ctx.guild.get_role(int(role))
                    if guild_role is not None:
                        roles_mapped.append(guild_role)
                excl = data.get(f"group{i}_excl")
                groups[group] = dict(roles=roles_mapped, id=i, excl=excl)
        return groups

    @cmd.guild_only()
    @checks.bot_has_perms(manage_roles=True)
    @cmd.group(name="sar", aliases=["iam"], invoke_without_command=True)
    async def sar(self, ctx):
        groups = await self.get_sars(ctx)
        if not groups:
            raise cmd.BadArgument("No self-assignable roles in this server. :<")

        embed = await self.bot.embed()
        embed.title = f"SAR groups for {ctx.guild}"
        for group, vals in groups.items():
            embed.add_field(name=vals["id"], value=group)
        m1 = await ctx.send(
            "Here are the available role groups. Please type a number to select a group.",
            embed=embed,
        )

        def check(message):
            return (
                ctx.author == message.author
                and ctx.guild == message.guild
                and message.content in [str(groups[g]["id"]) for g in groups]
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await m1.delete()
            raise cmd.BadArgument(
                "Query timed out. Exiting SAR. Type **{}{}** to return.".format(
                    ctx.prefix, ctx.invoked_with
                )
            )
        await m1.delete()

        get_group = next(
            (g for g in groups if str(groups[g]["id"]) == msg.content), None
        )
        print(get_group)
        embed = await self.bot.embed()
        embed.title = f"Avaliable roles for {get_group}"
        embed.description = "\n".join(
            [f"{i+1}. {r}" for i, r in enumerate(groups[get_group]["roles"])]
        )
        m2 = await ctx.send(
            f"Here are the roles for {get_group}. Please choose a number.", embed=embed
        )

        def check2(message):
            return (
                ctx.author == message.author
                and ctx.guild == message.guild
                and message.content
                in list(map(str, range(1, len(groups[get_group]["roles"]) + 1)))
            )

        try:
            msg = await self.bot.wait_for("message", check=check2, timeout=60.0)
        except asyncio.TimeoutError:
            await m2.delete()
            raise cmd.BadArgument(
                "Query timed out. Exiting SAR. Type **{}{}** to return.".format(
                    ctx.prefix, ctx.invoked_with
                )
            )
        await m2.delete()

        excl = groups[get_group]["excl"]
        roles = groups[get_group]["roles"]
        to_add = roles[int(msg.content) - 1]
        log = self.bot.get_cog("LoggingModule")
        if to_add in ctx.author.roles:
            raise cmd.BadArgument("You already have this role!")
        if to_add not in ctx.author.roles:
            if excl:
                to_remove = [r for r in roles if r in ctx.author.roles]
                await ctx.author.remove_roles(*to_remove)
                await log.on_member_role_remove(
                    ctx.guild,
                    ctx.guild.me,
                    ctx.author,
                    "Self-assigned",
                    to_remove,
                    mod=False,
                )
            await ctx.author.add_roles(to_add)
            await log.on_member_role_add(
                ctx.guild,
                ctx.guild.me,
                ctx.author,
                "Self-assigned.",
                [to_add],
                mod=False,
            )

        await ctx.send(f"Congrats {ctx.author.mention}, you got the **{to_add}** role!")

    @sar.group(name="group", aliases=["groups"], invoke_without_command=True)
    async def sar_group(self, ctx):
        groups = await self.get_sars(ctx)
        if not groups:
            raise cmd.BadArgument(
                "No SAR groups for {}. Add one with **{}sar group create <name>**".format(
                    ctx.guild, ctx.prefix
                )
            )
        embed = await self.bot.embed()
        embed.title = f"SAR groups for {ctx.guild}"
        for group, vals in groups.items():
            embed.add_field(
                name=f"{vals['id']}. {group} ({'' if vals['excl'] else 'non-'}exclusive)",
                value=", ".join([role.mention for role in vals["roles"]])
                or "None assigned.",
            )
        await ctx.send(embed=embed)

    @checks.is_mod()
    @checks.bot_has_perms(manage_roles=True)
    @sar_group.command(name="create")
    async def sar_group_create(self, ctx, name, excl: Optional[bool] = True):
        name = name[0:20]
        groups = await self.get_sars(ctx)
        if len(groups) > 4:
            raise cmd.BadArgument("5 group SAR limit reached.")
        if name.lower() in [g.lower() for g in list(groups.keys())]:
            raise cmd.BadArgument(f"SAR group with name {name} already exists.")
        next_free = next(
            (i for i in [1, 2, 3, 4, 5] if i not in [groups[g]["id"] for g in groups]),
            None,
        )
        if not groups:
            res = await self.bot.get_cog("PostgreModule").sql_insert(
                "sar",
                {
                    "id": ctx.guild.id,
                    f"group{next_free}_name": name,
                    f"group{next_free}_excl": excl,
                },
            )
        else:
            await self.bot.get_cog("PostgreModule").sql_update(
                "sar",
                ctx.guild.id,
                {
                    f"group{next_free}_name": name,
                    f"group{next_free}_excl": excl,
                    f"group{next_free}_roles": "",
                },
            )

        await ctx.send(f":white_check_mark: Created SAR group #{next_free}: {name}")

    @checks.is_mod()
    @checks.bot_has_perms(manage_roles=True)
    @sar_group.command(name="delete")
    async def sar_group_delete(self, ctx, name):
        groups = await self.get_sars(ctx)
        if not groups:
            raise cmd.BadArgument("No SAR groups exist.")

        print(groups)
        group_to_edit = next((g for g in groups if g.lower() == name.lower()), None)
        print(group_to_edit)
        if group_to_edit is None:
            raise cmd.BadArgument(f"SAR group with name {name} does not exist.")
        to_delete = groups[group_to_edit]["id"]
        await self.bot.get_cog("PostgreModule").sql_update(
            "sar",
            ctx.guild.id,
            {
                f"group{to_delete}_name": None,
                f"group{to_delete}_excl": None,
                f"group{to_delete}_roles": None,
            },
        )
        await ctx.send(
            ":white_check_mark: Successfully deleted group #{}: {}".format(
                to_delete, name
            )
        )

    @checks.is_mod()
    @checks.bot_has_perms(manage_roles=True)
    @sar_group.command(name="rename")
    async def sar_group_rename(self, ctx, name, newname):
        groups = await self.get_sars(ctx)
        if not groups:
            raise cmd.BadArgument("No SAR groups exist.")
        group_to_edit = next((g for g in groups if g.lower() == name.lower()), None)
        if group_to_edit is None:
            raise cmd.BadArgument(f"SAR group with name {name} does not exist.")
        to_edit = groups[group_to_edit]["id"]
        await self.bot.get_cog("PostgreModule").sql_update(
            "sar", ctx.guild.id, {f"group{to_edit}_name": newname[0:20]}
        )
        await ctx.send(
            ":white_check_mark: Successfully renamed group #{} from **{}** to **{}**".format(
                to_edit, name, newname[0:20]
            )
        )

    @checks.is_mod()
    @checks.bot_has_perms(manage_roles=True)
    @sar_group.command(name="add")
    async def sar_group_add(self, ctx, group, *roles: cmd.Greedy[cmd.RoleConverter]):
        group = group[0:20]
        groups = await self.get_sars(ctx)
        if not groups:
            raise cmd.BadArgument("No SAR groups exist.")
        group_to_edit = next((g for g in groups if g.lower() == group.lower()), None)
        if group_to_edit is None:
            raise cmd.BadArgument(f"SAR group with name {group} does not exist.")
        if roles is None or not roles:
            raise cmd.BadArgument("You need to specify some roles to add!")
        old_roles = groups[group_to_edit]["roles"]
        to_add = [r for r in roles if r not in old_roles]
        if not to_add:
            raise cmd.BadArgument("All roles specified are already in this group!")
        not_allowed = [r for r in to_add if r > ctx.author.top_role]
        if not_allowed:
            raise cmd.BadArgument(
                "You can only add roles lower than your own to SAR groups."
            )
        to_add = old_roles + to_add
        to_edit = groups[group_to_edit]["id"]
        await self.bot.get_cog("PostgreModule").sql_update(
            "sar",
            ctx.guild.id,
            {f"group{to_edit}_roles": " ".join(str(r.id) for r in to_add)},
        )
        await ctx.send(
            ":white_check_mark: Successfully added roles to group #{} **{}**: {}".format(
                to_edit, group, ", ".join([f"@**{r}**" for r in roles])
            )
        )

    @checks.is_mod()
    @checks.bot_has_perms(manage_roles=True)
    @sar_group.command(name="remove")
    async def sar_group_remove(self, ctx, group, *roles: cmd.Greedy[cmd.RoleConverter]):
        group = group[0:20]
        groups = await self.get_sars(ctx)
        if not groups:
            raise cmd.BadArgument("No SAR groups exist.")
        group_to_edit = next((g for g in groups if g.lower() == group.lower()), None)
        if group_to_edit is None:
            raise cmd.BadArgument(f"SAR group with name {group} does not exist.")
        if roles is None or not roles:
            raise cmd.BadArgument("You need to specify some roles to delete!")
        old_roles = groups[group_to_edit]["roles"]
        to_del = [r for r in roles if r in old_roles]
        if not to_del:
            raise cmd.BadArgument("No roles specified are in this group!")
        not_allowed = [r for r in to_del if r > ctx.author.top_role]
        if not_allowed:
            raise cmd.BadArgument(
                "You can only remove roles lower than your own from SAR groups."
            )
        to_keep = [r for r in old_roles if r not in to_del]
        to_edit = groups[group_to_edit]["id"]
        await self.bot.get_cog("PostgreModule").sql_update(
            "sar",
            ctx.guild.id,
            {f"group{to_edit}_roles": " ".join(str(r.id) for r in to_keep)},
        )
        plural = "s" if len(to_del) != 1 else ""
        await ctx.send(
            ":white_check_mark: Successfully removed role{} from group #{} **{}**: {}".format(
                plural, to_edit, group, ", ".join([f"@**{r}**" for r in roles])
            )
        )


def setup(bot):
    bot.add_cog(SarModule(bot))
