from discord.ext import commands as cmd


class GreetModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.Cog.listener()
    async def on_member_join(self, member):
        greet_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "greet")
        if greet_is_on in (None, "0"):
            return
        greet_msg = await self.bot.db.hget(f"{member.guild.id}:set", "grt")
        greet_chan = await self.bot.db.hget(f"{member.guild.id}:set", "greetchannel")
        if not greet_msg or not greet_chan:
            return
        chan = self.bot.get_channel(int(greet_chan))
        if not chan:
            await self.bot.db.hset(f"{member.guild.id}:toggle", "greet", "0")
            return
        await chan.send(
            greet_msg.format(
                user=str(member), server=str(member.guild), mention=member.mention
            )
        )

    @cmd.Cog.listener()
    async def on_member_remove(self, member):
        greet_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "goodbye")
        if greet_is_on in (None, "0"):
            return
        greet_msg = await self.bot.db.hget(f"{member.guild.id}:set", "dpt")
        greet_chan = await self.bot.db.hget(f"{member.guild.id}:set", "goodbyechannel")
        if not greet_msg or not greet_chan:
            return
        chan = self.bot.get_channel(int(greet_chan))
        if not chan:
            await self.bot.db.hset(f"{member.guild.id}:toggle", "goodbye", "0")
            return
        await chan.send(
            greet_msg.format(
                user=str(member), server=str(member.guild), mention=member.mention
            )
        )


def setup(bot):
    bot.add_cog(GreetModule(bot))
