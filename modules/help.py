import discord
from discord.ext import commands as cmd

# import difflib


class HelpModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command(name="help", aliases=["h"], usage="<module> <command>")
    async def help(self, ctx, *command):
        "Displays help about stuff."
        icon = self.bot.get_cog("TapTitansModule").emoji("orange_question")
        fields = {}
        if not command:
            title = f"Available modules for {self.bot.user}"
            description = ", ".join(
                [f"{c.replace('Module', '')}" for c in self.bot.cogs]
            )
        else:
            command = list(command)
            cog = [
                c
                for c, v in self.bot.cogs.items()
                if str(c).lower().startswith(command[0].lower())
                or command[0].lower() in getattr(v, "aliases", [])
            ]
            if not cog:
                raise cmd.BadArgument(f"No module with name: **{command[0].lower()}**")
            if len(cog) > 1:
                raise cmd.BadArgument(
                    "I found multiple modules. Please try to narrow your search: {}".format(
                        ", ".join(
                            [f"**{c.replace('Module', '').lower()}**" for c in cog]
                        )
                    )
                )
            command = [cog[0].replace("Module", "").lower()] + command[1:]
            cx = next(
                (
                    s
                    for s in self.bot.walk_commands()
                    if " ".join(command) == str(s)
                    or command[-1] in s.aliases
                    and not hasattr(s, "walk_commands")
                ),
                None,
            )
            if cx is None:
                cx = self.bot.get_command(command[-1])
            if cx is not None and len(command) > 1:
                title = f"Help for command **{ctx.prefix}{cx}**"
                description = cx.help or "No help file found."
                usg = (
                    f"{ctx.prefix}{' '.join(command)} {' '.join((f'<{x}>' for x in cx.usage.split()))}"
                    if cx.usage
                    else ""
                )
                fields["Usage"] = usg or "No usage found."
            else:
                cg = self.bot.get_cog(cog[0])
                subcommands = list(cg.walk_commands())
                module = cg.qualified_name.replace("Module", "").lower()
                groups, commands = [], []
                for sub in subcommands:
                    strsub = str(sub)
                    if hasattr(sub, "walk_commands") and not strsub == module:
                        groups.append(strsub.replace(module, "").strip())
                    elif len(strsub.split()) < 3:
                        if not module in strsub:
                            commands.append(strsub)
                        elif strsub.replace(module, ""):
                            commands.append(strsub.replace(module, ""))
                aliases = ", ".join(getattr(cg, "aliases", []))
                title = f"Help for **{module}** module"
                description = cg.__doc__ or "No helpfile found."
                if aliases:
                    fields["Aliases"] = aliases
                if groups:
                    fields["Command Groups"] = ", ".join(set(groups))
                if commands:
                    fields["Commands"] = ", ".join(set(commands))

        embed = discord.Embed(title=title, description=description, color=0xF89D2A)
        if fields:
            for field in fields:
                embed.add_field(name=field, value=fields[field])

        embed.set_thumbnail(url=icon.url)
        await ctx.send("", embed=embed)


def setup(bot):
    bot.add_cog(HelpModule(bot))
