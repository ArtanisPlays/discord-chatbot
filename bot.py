import os
import logging

import discord
from discord.ext import commands

from services.llm_client import LLMClient

logger = logging.getLogger("DiscordBot")


class CustomBot(commands.Bot):
    """Central bot class: holds shared services and cross-guild state."""

    def __init__(self):
        super().__init__(
            command_prefix=os.getenv("BOT_PREFIX", "!"),
            intents=self._default_intents(),
            help_command=None,  # custom /help slash command
        )
        # Shared chat API client, used by all cogs.
        self.llm = LLMClient()
        # Per-guild model override: {guild_id: model_id}
        self.guild_models: dict[int, str] = {}

    @staticmethod
    def _default_intents() -> discord.Intents:
        intents = discord.Intents.default()
        intents.message_content = True  # required to read message content
        return intents

    def effective_model(self, guild_id: int | None) -> str:
        """The model active in a guild, or the global default."""
        if guild_id and guild_id in self.guild_models:
            return self.guild_models[guild_id]
        return self.llm.model

    def set_guild_model(self, guild_id: int, model: str) -> None:
        self.guild_models[guild_id] = model

    def reset_guild_model(self, guild_id: int) -> None:
        self.guild_models.pop(guild_id, None)

    async def setup_hook(self):
        """Load all cogs from the cogs directory before connecting."""
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        if os.path.exists(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    cog_name = f"cogs.{filename[:-3]}"
                    try:
                        await self.load_extension(cog_name)
                        logger.info(f"Loaded cog extension: {cog_name}")
                    except Exception as e:
                        logger.error(f"Failed to load cog extension {cog_name}: {e}", exc_info=True)

        # Sync application slash commands with Discord
        try:
            logger.info("Syncing slash commands...")
            synced = await self.tree.sync()
            logger.info(f"Successfully synced {len(synced)} slash command(s) globally.")
        except Exception as e:
            logger.error(f"Error syncing slash commands: {e}", exc_info=True)

    async def on_ready(self):
        """Triggered when the bot is connected and ready."""
        logger.info(f"🤖 Logged in as: {self.user.name} (ID: {self.user.id})")
        logger.info(f"🌐 Connected to {len(self.guilds)} guild(s)")

        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="@ me to chat! | /help"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global error handler for prefix commands."""
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error in '{ctx.command}': {error}")
        await ctx.send(f"⚠️ Error: `{error}`")
