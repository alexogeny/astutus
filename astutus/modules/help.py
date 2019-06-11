import discord
from discord.ext import commands as cmd


class HelpModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command(name="help", aliases=["h"])
    async def help(self, ctx, *command):
        if not command:
            st = "Currently available modules for **{}**. Type **{}{} <module>** (without brackets) to access the help page for a module:\n{{}}".format(
                self.bot.user.mention, ctx.prefix, ctx.command
            )
            hlp = ", ".join([f"**{c.replace('Module', '')}**" for c in self.bot.cogs])
            await ctx.send(st.format(hlp))
            return
        cog = [
            c for c in self.bot.cogs if str(c).lower().startswith(command[0].lower())
        ]
        if not cog:
            if len(command) <= 1:
                await ctx.send(
                    "Sorry, I could not find a module by the name: **{}**".format(
                        command[0].lower()
                    )
                )
                return
        if len(command) > 1 and " ".join(command) in [
            str(s) for s in self.bot.walk_commands()
        ]:
            result = "Help for command **{}{}**\n\nDescription:\n{}\n\nUsage:\n{}"
            cx = self.bot.get_command(" ".join(command))
            await ctx.send(
                result.format(
                    ctx.prefix, cx, cx.help or "No help file found.", "random"
                )
            )
        elif len(cog) > 1:
            await ctx.send(
                "I found multiple modules. Please try to narrow your search: {}".format(
                    ", ".join([f"**{c.replace('Module', '').lower()}**" for c in cog])
                )
            )
            return
        cg = self.bot.get_cog(cog[0])
        subcommands = list(cg.walk_commands())
        module = cg.qualified_name.replace("Module", "").lower()
        cmd_grp = [
            s
            for s in subcommands
            if hasattr(s, "walk_commands") and not str(s) == module
        ]
        cmd_lst = [
            s
            for s in subcommands
            if not s.hidden and not s.parent or str(s.parent) == module
        ]
        await ctx.send(
            "Help for **{}** module:\n\n**Description**\n{}\n\n**Command Groups**\n{}\n\n**Commands**\n{}{}".format(
                module,
                cg.__doc__ or "none found.",
                cmd_grp
                and ", ".join([str(s) for s in cmd_grp])
                or "No command groups for this module.",
                cmd_lst
                and ", ".join([str(s) for s in cmd_lst])
                or "No individual commands for this module.",
                cmd_grp
                and "\n\nPS: To get help for a command group, follow this example: **{}help {}**".format(
                    ctx.prefix, next(cmd_grp[0].walk_commands(), None)
                )
                or "",
            )
        )


def setup(bot):
    bot.add_cog(HelpModule(bot))
