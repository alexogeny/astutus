from discord.ext import commands as cmd
from astutus.utils.checks import is_bot_owner
import time

# import psutil
import discord
import importlib
import os
import glob


class CogNotFoundError(Exception):
    pass


class CogLoadError(Exception):
    pass


class NoSetupError(CogLoadError):
    pass


class CogUnloadError(Exception):
    pass


class OwnerUnloadWithoutReloadError(CogUnloadError):
    pass


class UtilityModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command()
    async def ping(self, ctx):
        msg = "It's just a song about ping pong ..."
        before = time.monotonic()
        ping_message = await ctx.send(msg)
        after = time.monotonic()
        ping = (after - before) * 1000
        try:
            await ping_message.edit(content=f"{msg} **({ping:.0f} ms)**")
        except:
            await ctx.send(f"**{ping:.0f} ms**")

    @cmd.command()
    @is_bot_owner()
    async def load(self, ctx: cmd.Context, *, module: str):
        if "astutus.modules" not in module:
            module = f"astutus.modules.{module}"
        try:
            self._load_cog(module)
        except CogNotFoundError:
            await ctx.send("That cog could not be found.")
        except CogLoadError:
            await ctx.send("There was an error loading the cog. Check your logs.")
        else:
            await ctx.send("loaded the cog")

    @cmd.command()
    @is_bot_owner()
    async def reload(self, ctx: cmd.Context, *, module: str):
        if "astutus.modules" not in module:
            module = f"astutus.modules.{module}"
        try:
            self._unload_cog(module, reloading=True)
        except:
            pass

        try:
            self._load_cog(module)
        except CogNotFoundError:
            await ctx.send("That cog cannot be found.")
        except NoSetupError:
            await ctx.send("That cog does not have a setup function.")
        except CogLoadError:
            await ctx.send("There was an error reloading the cog. Check your logs.")
        else:
            await ctx.send("The cog has been reloaded.")

    def _load_cog(self, cogname):
        if not self._does_cogfile_exist(cogname):
            raise CogNotFoundError(cogname)
        try:
            mod_obj = importlib.import_module(cogname)
            importlib.reload(mod_obj)
            self.bot.load_extension(mod_obj.__name__)
        except SyntaxError as e:
            raise CogLoadError(*e.args)
        except:
            raise

    def _unload_cog(self, cogname, reloading=False):
        if not reloading and cogname == "astutus.modules.utils":
            raise OwnerUnloadWithoutReloadError(
                "Can't permanently unload the utils plugin :P"
            )
        try:
            self.bot.unload_extension(cogname)
        except:
            raise CogUnloadError

    def _list_cogs(self):
        cogs = [os.path.basename(f) for f in glob.glob("astutus/modules/*.py")]
        return ["astutus.modules." + os.path.splitext(f)[0] for f in cogs]

    def _does_cogfile_exist(self, module):
        if "astutus.modules." not in module:
            module = "astutus.modules." + module
        if module not in self._list_cogs():
            return False
        return True


def setup(bot):
    bot.add_cog(UtilityModule(bot))
