import discord
from discord import commands as discord_commands
from discord.ext import commands


class ModelCog(commands.Cog):
    """Commands to view and switch the chat model used by the bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _model_autocomplete(self, ctx: discord.AutocompleteContext):
        models = await self.bot.model_service.list_models()
        current = (ctx.value or "").lower()
        choices = []
        for m in models:
            label = f"{m['name']} ({m['id']})" if m["name"] != m["id"] else m["id"]
            if current in label.lower():
                choices.append(discord_commands.OptionChoice(name=label, value=m["id"]))
            if len(choices) >= 25:
                break
        return choices

    model_group = discord.SlashCommandGroup(name="model", description="View or change the chat model used by the bot.")

    @model_group.command(name="show", description="Show the chat model currently used in this server.")
    @discord.guild_only()
    async def model_show(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="Current Chat Model", color=discord.Color.blurple())
        embed.add_field(name="Server override", value=f"`{self.bot.model_service.effective_model(ctx.guild_id)}`", inline=False)
        embed.add_field(name="Global default", value=f"`{self.bot.model_service.provider.model}`", inline=False)
        embed.set_footer(text="Use /model list to see all available models.")
        await ctx.respond(embed=embed)

    @model_group.command(name="list", description="List every model available on the chat API.")
    @discord.guild_only()
    async def model_list(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        models = await self.bot.model_service.list_models()

        if not models:
            await ctx.followup.send(
                "Could not fetch the model list. Is `CHAT_API_URL` configured and the API reachable?"
            )
            return

        current = self.bot.model_service.effective_model(ctx.guild_id)
        lines = []
        for m in models:
            if m["id"] == current:
                lines.append(f"* **{m['name']}** *(active in this server)*\n  `{m['id']}`")
            else:
                lines.append(f"• **{m['name']}**\n  `{m['id']}`")
        text = "\n".join(lines)

        embed = discord.Embed(
            title=f"Available Models ({len(models)})",
            description="The model marked with * is currently active in this server.",
            color=discord.Color.blurple(),
        )
        if len(text) <= 1024:
            embed.add_field(name="Models", value=text, inline=False)
            await ctx.followup.send(embed=embed)
        else:
            pages = [text[i:i + 1024] for i in range(0, len(text), 1024)]
            for i, page in enumerate(pages, start=1):
                page_embed = discord.Embed(title=f"Models ({i}/{len(pages)})", color=discord.Color.blurple())
                page_embed.add_field(name="Models", value=page, inline=False)
                await ctx.followup.send(embed=page_embed)

    @model_group.command(name="set", description="Set the chat model used by the bot in this server.")
    @discord.option("model", description="The model id to use (e.g. gpt-oss:20b)", autocomplete=_model_autocomplete)
    @discord.guild_only()
    async def model_set(self, ctx: discord.ApplicationContext, model: str):
        await ctx.defer()
        models = await self.bot.model_service.list_models()

        valid_ids = {m["id"] for m in models}
        if valid_ids and model not in valid_ids:
            await ctx.followup.send(
                f"`{model}` is not in the model list. Use `/model list` to see valid models.",
                ephemeral=True,
            )
            return

        self.bot.model_service.set_guild_model(ctx.guild_id, model)
        embed = discord.Embed(
            title="Model Updated",
            description=f"This server's chat model is now **`{model}`**.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Use /model reset to go back to the global default.")
        await ctx.followup.send(embed=embed)

    @model_group.command(name="reset", description="Reset this server's model back to the global default.")
    @discord.guild_only()
    async def model_reset(self, ctx: discord.ApplicationContext):
        override = self.bot.model_service.effective_model(ctx.guild_id) != self.bot.model_service.provider.model
        if override:
            self.bot.model_service.reset_guild_model(ctx.guild_id)
            embed = discord.Embed(
                title="Model Reset",
                description=f"Back to the global default: **`{self.bot.model_service.provider.model}`**",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="No Override",
                description=f"This server already uses the global default: **`{self.bot.model_service.provider.model}`**",
                color=discord.Color.blurple(),
            )
        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(ModelCog(bot))
