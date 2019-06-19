from discord.ext import commands as cmd
from .utils import checks, chat_formatting
import time

# import psutil
import discord
import importlib
import os
import glob
from urllib.parse import quote_plus
import aiohttp

# from utils import chat_formatting


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
    async def invite(self, ctx, kind: str = "admin"):
        if kind.lower() not in "admin.normal":
            await ctx.send("Choose between **admin**/**normal** for bot invite links.")
            return
        await ctx.send(f"{kind.title()} link: <{getattr(self.bot, f'link_{kind}')}>")

    @cmd.command(aliases=["dictionary", "d"])
    async def define(self, ctx, word: str):
        if not word:
            return

    @cmd.command(aliases=["ud"])
    @cmd.guild_only()
    async def urban(self, ctx, *, search_terms: str, definition_number: int = 1):
        """Search Urban Dictionary"""

        # if not ctx.channel.is_nsfw():
        #     return await ctx.send("Please use this in an NSFW channel.", delete_after=5)

        def encode(s):
            return quote_plus(s, encoding="utf-8", errors="replace")

        search_terms = search_terms.split(" ")
        try:
            if len(search_terms) > 1:
                pos = int(search_terms[-1]) - 1
                search_terms = search_terms[:-1]
            else:
                pos = 0
            if pos not in range(0, 11):
                pos = 0
        except ValueError:
            pos = 0

        search_terms = "+".join([encode(s) for s in search_terms])
        url = "http://api.urbandictionary.com/v0/define?term=" + search_terms
        try:
            async with aiohttp.ClientSession() as cs:
                async with cs.get(url) as r:
                    result = await r.json()
            if result["list"]:
                definition = result["list"][pos]["definition"]
                example = result["list"][pos]["example"]
                defs = len(result["list"])
                msg = "**Definition #{} out of {}:\n**{}\n\n" "**Example:\n**{}".format(
                    pos + 1, defs, definition, example
                )
                msg = chat_formatting.pagify(msg, ["\n"])
                for page in msg:
                    await ctx.send(page)
            else:
                await ctx.send("Your search terms gave no results.")
        except IndexError:
            await ctx.send("There is no definition #{}".format(pos + 1))

    @cmd.command()
    @checks.is_bot_owner()
    async def shutdown(self, ctx, when: str = None):
        await self.bot.logout()

    @cmd.command()
    @checks.is_bot_owner()
    async def redisclear(self, ctx, key):
        result = await self.bot.db.delete(key.format(ctx))
        await ctx.send(str(result))

    @cmd.command()
    @checks.is_bot_owner()
    async def load(self, ctx: cmd.Context, *, module: str):
        if "astutus.modules" not in module:
            module = f"modules.{module}"
        try:
            self._load_cog(module)
        except CogNotFoundError:
            await ctx.send("That cog could not be found.")
        except CogLoadError:
            await ctx.send("There was an error loading the cog. Check your logs.")
        else:
            await ctx.send("loaded the cog")

    @cmd.command()
    @checks.is_bot_owner()
    async def reload(self, ctx: cmd.Context, *, module: str):
        if "modules" not in module:
            module = f"modules.{module}"
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
        if not reloading and cogname == "modules.utility":
            raise OwnerUnloadWithoutReloadError(
                "Can't permanently unload the utils plugin :P"
            )
        try:
            self.bot.unload_extension(cogname)
        except:
            raise CogUnloadError

    def _list_cogs(self):
        cogs = [os.path.basename(f) for f in glob.glob("modules/*.py")]
        return ["modules." + os.path.splitext(f)[0] for f in cogs]

    def _does_cogfile_exist(self, module):
        if "modules." not in module:
            module = "modules." + module
        if module not in self._list_cogs():
            return False
        return True


def setup(bot):
    bot.add_cog(UtilityModule(bot))
