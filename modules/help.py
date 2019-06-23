# import discord
from discord.ext import commands as cmd

# import difflib


class HelpModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command(name="help", aliases=["h"], usage="<module> <command>")
    async def help(self, ctx, *command):
        "Displays help about stuff."
        if not command:
            support_text = "Currently available modules for **{}**. Type **{}{} <module>** (without brackets) to access the help page for a module:\n{{}}".format(
                self.bot.user.mention, ctx.prefix, ctx.command
            )
            hlp = ", ".join([f"**{c.replace('Module', '')}**" for c in self.bot.cogs])
            await ctx.send(support_text.format(hlp))
            return
        command = list(command)
        cog = [
            c
            for c, v in self.bot.cogs.items()
            if str(c).lower().startswith(command[0].lower())
            or command[0].lower() in getattr(v, "aliases", [])
        ]
        if not cog:
            raise cmd.BadArgument(f"No module with name: **{command[0].lower()}**")
        command = [cog[0].replace("Module", "").lower()] + command[1:]
        cx = next(
            (
                s
                for s in self.bot.walk_commands()
                if " ".join(command) == str(s) or command[-1] in s.aliases
            ),
            None,
        )
        if len(command) > 1 and cx is not None:
            result = "Help for command **{}{}**\n\n**Description**\n{}\n\n**Usage**\n{}"
            usg = (
                cx.usage
                and f"{ctx.prefix}{' '.join(command)} {' '.join(f'<{x}>' for x in cx.usage.split())}"
                or ""
            )
            await ctx.send(
                result.format(
                    ctx.prefix,
                    cx,
                    cx.help or "No help file found.",
                    usg or "No usage found.",
                )
            )
            return
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
        cmd_grp = ", ".join(
            set(
                [
                    str(s).replace(module, "").strip()
                    for s in subcommands
                    if hasattr(s, "walk_commands") and not str(s) == module
                ]
            )
        )
        cmd_lst = ", ".join(
            set(
                [
                    str(s).replace(module, "").strip()
                    for s in subcommands
                    if len(str(s).split()) == 2 and not hasattr(s, "walk_commands")
                ]
            )
        )
        aliases = ", ".join(getattr(cg, "aliases", []))
        cmd_grp = cmd_grp and f"**Command Groups**\n{cmd_grp}\n\n" or ""
        cmd_lst = cmd_lst and f"**Commands**\n{cmd_lst}\n\n" or ""
        await ctx.send(
            "Help for **{}** module:\n\n**Description**\n{}\n\n{}{}{}".format(
                module,
                cg.__doc__ or "none found.",
                aliases and f"**Aliases**\n{aliases}\n\n" or "",
                cmd_grp,
                cmd_lst,
            )
        )


def setup(bot):
    bot.add_cog(HelpModule(bot))
