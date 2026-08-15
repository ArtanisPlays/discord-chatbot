import time

import discord
from discord import app_commands
from discord.ext import commands


class ModelCog(commands.Cog):
    """Commands to view and switch the chat model used by the bot."""

    MODELS_CACHE_TTL = 300  # seconds

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._models_cache: list[dict] = []
        self._models_cached_at: float = 0.0

    async def _get_models(self) -> list[dict]:
        """Fetch the model list, caching briefly to avoid hammering the API."""
        now = time.monotonic()
        if not self._models_cache or now - self._models_cached_at > self.MODELS_CACHE_TTL:
            self._models_cache = await self.bot.llm.fetch_models()
            self._models_cached_at = now
        return self._models_cache

    async def _model_autocomplete(self, interaction: discord.Interaction, current: str):
        models = await self._get_models()
        choices = []
        for m in models:
            label = f"{m['name']} ({m['id']})" if m["name"] != m["id"] else m["id"]
            if current.lower() in label.lower():
                choices.append(app_commands.Choice(name=label, value=m["id"]))
            if len(choices) >= 25:
                break
        return choices

    model_group = app_commands.Group(name="model", description="View or change the chat model used by the bot.")

    @model_group.command(name="show", description="Show the chat model currently used in this server.")
    @app_commands.guild_only()
    async def model_show(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Current Chat Model", color=discord.Color.blurple())
        embed.add_field(name="Server override", value=f"`{self.bot.effective_model(interaction.guild_id)}`", inline=False)
        embed.add_field(name="Global default", value=f"`{self.bot.llm.model}`", inline=False)
        embed.set_footer(text="Use /model list to see all available models.")
        await interaction.response.send_message(embed=embed)

    @model_group.command(name="list", description="List every model available on the chat API.")
    @app_commands.guild_only()
    async def model_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        models = await self._get_models()

        if not models:
            await interaction.followup.send(
                "Could not fetch the model list. Is `CHAT_API_URL` configured and the API reachable?"
            )
            return

        current = self.bot.effective_model(interaction.guild_id)
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
            await interaction.followup.send(embed=embed)
        else:
            pages = [text[i:i + 1024] for i in range(0, len(text), 1024)]
            for i, page in enumerate(pages, start=1):
                page_embed = discord.Embed(title=f"Models ({i}/{len(pages)})", color=discord.Color.blurple())
                page_embed.add_field(name="Models", value=page, inline=False)
                await interaction.followup.send(embed=page_embed)

    @model_group.command(name="set", description="Set the chat model used by the bot in this server.")
    @app_commands.describe(model="The model id to use (e.g. gpt-oss:20b)")
    @app_commands.guild_only()
    @app_commands.autocomplete(model=_model_autocomplete)
    async def model_set(self, interaction: discord.Interaction, model: str):
        await interaction.response.defer()
        models = await self._get_models()

        valid_ids = {m["id"] for m in models}
        if valid_ids and model not in valid_ids:
            await interaction.followup.send(
                f"`{model}` is not in the model list. Use `/model list` to see valid models.",
                ephemeral=True,
            )
            return

        self.bot.set_guild_model(interaction.guild_id, model)
        embed = discord.Embed(
            title="Model Updated",
            description=f"This server's chat model is now **`{model}`**.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Use /model reset to go back to the global default.")
        await interaction.followup.send(embed=embed)

    @model_group.command(name="reset", description="Reset this server's model back to the global default.")
    @app_commands.guild_only()
    async def model_reset(self, interaction: discord.Interaction):
        override = self.bot.effective_model(interaction.guild_id) != self.bot.llm.model
        if override:
            self.bot.reset_guild_model(interaction.guild_id)
            embed = discord.Embed(
                title="Model Reset",
                description=f"Back to the global default: **`{self.bot.llm.model}`**",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(
                title="No Override",
                description=f"This server already uses the global default: **`{self.bot.llm.model}`**",
                color=discord.Color.blurple(),
            )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModelCog(bot))
