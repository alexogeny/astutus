"""Todo module."""

from typing import Optional
from discord.ext import commands as cmd


class TodoModule(cmd.Cog):
    """Manage your todo list! You can have up to 10 todos."""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.group(name="todo", aliases=["todos"], invoke_without_command=True)
    async def todo(self, ctx):
        """Inspect your todo list."""
        my_todos = await self.bot.db.lrange(f"{ctx.author.id}:todo")
        if not my_todos:
            await ctx.send(
                f"Good job **{ctx.author}**, looks like you do not have any todos!"
            )
            return
        result = []
        for i, todo in enumerate(my_todos):
            result.append(f"**{i+1}**. {todo}")

        await ctx.send(
            "Ok **{}**, here's your todo list:\n{}".format(
                ctx.author, "\n".join(result)
            )
        )

    @todo.command(name="add", aliases=["a"])
    async def todo_add(self, ctx, *todo):
        """Add a new todo."""
        todo = " ".join(todo)
        if len(todo) > 140:
            raise cmd.BadArgument("Please specify a todo in less than 140 characters.")
        my_todos = await self.bot.db.lrange(f"{ctx.author.id}:todo")
        if len(my_todos) == 10:
            raise cmd.BadArgument("You cannot have more than 10 todos at a time.")

        await self.bot.db.rpush(f"{ctx.author.id}:todo", todo)
        await ctx.send(f"Successfully added #**{len(my_todos)+1}** to your todo list.")

    @todo.command(name="remove", aliases=["rem", "r", "done"])
    async def todo_done(self, ctx, todo: Optional[int]):
        """Mark a todo as done."""
        if not todo:
            raise cmd.BadArgument("You need to choose a todo to delete.")
        my_todos = await self.bot.db.lrange(f"{ctx.author.id}:todo")
        if not my_todos:
            raise cmd.BadArgument("You do not currently have any todos!")
        if len(my_todos) < todo:
            raise cmd.BadArgument(
                f"I could not find a todo with that number. You have **{len(my_todos)}** todos."
            )
        to_rem = my_todos[todo - 1]
        await self.bot.db.lrem(f"{ctx.author.id}:todo", to_rem)
        if len(my_todos) == 1:
            await ctx.send(
                f"Good job **{ctx.author}**, looks like you do not have any todos!"
            )
        else:
            await ctx.send(f"You have **{len(my_todos)-1}** todos remaining.")


def setup(bot):
    """Bind the module to the bot."""
    bot.add_cog(TodoModule(bot))
