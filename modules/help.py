import json
import discord
from discord.ext import commands as cmd

with open("modules/data/Help.json", "r") as jf:
    HELP = json.load(jf)


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
                [
                    f"{c.replace('Module', '')}"
                    for c in self.bot.cogs
                    if str(c) != "PostgreModule"
                ]
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
            cx = self.bot.get_command(" ".join(command))

            if cx is not None and len(command) > 1:
                title = f"Help for command **{ctx.prefix}{cx}**"
                obj = HELP.get(str(cx), {})
                description = obj.get("desc", "Not found.")
                fields["Usage"] = (
                    "\n".join([f"{ctx.prefix}{u}" for u in obj.get("usage", [])])
                    or "Not found."
                )
                aliases = ", ".join(getattr(cx, "aliases", []))
                if aliases:
                    fields["Aliases"] = aliases
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
                        if not module in strsub and not sub.hidden:
                            commands.append(strsub)
                        elif strsub.replace(module, "") and not sub.hidden:
                            commands.append(strsub.replace(module, ""))
                aliases = ", ".join(getattr(cg, "aliases", []))
                title = f"Help for **{module}** module"
                obj = HELP.get(str(cg.qualified_name).replace("Module", "").lower(), {})
                description = (
                    obj.get("desc", None) or cg.__doc__ or "No helpfile found."
                )
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
        if not command:
            cstm = await self.bot.db.hget(f"{ctx.guild.id}:set", "pfx")
            if not cstm or cstm is None:
                cstm = ""
            pfx = str(cstm) if cstm else self.bot.config["DEFAULT"]["prefix"]
            embed.add_field(name="Current Prefix", value=pfx)
        embed.set_thumbnail(url=icon.url)
        await ctx.send("", embed=embed)


def setup(bot):
    bot.add_cog(HelpModule(bot))
