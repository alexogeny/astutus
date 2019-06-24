import discord
from discord.ext import commands as cmd

# import difflib


class HelpModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command(name="help", aliases=["h"], usage="<module> <command>")
    async def help(self, ctx, *command):
        "Displays help about stuff."
        if not command:
            embed = discord.Embed(
                title=f'Available modules for {self.bot.user}',
                description=", ".join([f"{c.replace('Module', '')}" for c in self.bot.cogs])
            )
            await ctx.send("", embed=embed)
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
            embed = discord.Embed(
                title=f'Help for command **{ctx.prefix}{cx}**',
                description=cx.help or "No help file found."
            )
            usg = (
                f"{ctx.prefix}{' '.join(command)} {' '.join((f'<{x}>' for x in cx.usage.split()))}"
                if cx.usage else ''
            )
            embed.add_field(
                name='Usage',
                value=usg or "No usage found."
            )
            await ctx.send('', embed=embed)
            return
        if len(cog) > 1:
            raise cmd.BadArgument(
                "I found multiple modules. Please try to narrow your search: {}".format(
                    ", ".join([f"**{c.replace('Module', '').lower()}**" for c in cog])
                )
            )
        cg = self.bot.get_cog(cog[0])
        subcommands = list(cg.walk_commands())
        module = cg.qualified_name.replace("Module", "").lower()
        cmd_grp = ", ".join(
            {
                str(s).replace(module, "").strip()
                for s in subcommands
                if hasattr(s, "walk_commands") and not str(s) == module
            }
        )
        cmd_lst = ", ".join(
            {
                str(s).replace(module, "").strip()
                for s in subcommands
                if len(str(s).split()) in [1, 2] and not hasattr(s, "walk_commands")
            }
        )
        aliases = ", ".join(getattr(cg, "aliases", []))
        embed = discord.Embed(
            title=f'Help for **{module}** module',
            description=cg.__doc__ or "No helpfile found."
        )
        if aliases:
            embed.add_field(name='Aliases', value=aliases, inline=False)
        if cmd_grp:
            embed.add_field(name='Command Groups', value=cmd_grp)
        if cmd_lst:
            embed.add_field(name='Commands', value=cmd_lst)
        await ctx.send("", embed=embed)


def setup(bot):
    bot.add_cog(HelpModule(bot))
