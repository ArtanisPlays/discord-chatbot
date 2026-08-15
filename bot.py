import os
import time
import logging

import discord
from discord.ext import commands

from config import get_dev_guild_id
from services.llm_client import LLMClient

logger = logging.getLogger("DiscordBot")

# Conversation memory settings (can be tuned via .env).
HISTORY_MAX_MESSAGES = int(os.getenv("CHAT_HISTORY_MESSAGES", "20"))
HISTORY_TTL_SECONDS = int(os.getenv("CHAT_HISTORY_TTL", "1800"))  # idle reset


async def load_cogs(bot: commands.Bot) -> None:
    """Load every cog from the cogs directory."""
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await bot.load_extension(cog_name)
                    logger.info(f"Loaded cog extension: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load cog extension {cog_name}: {e}", exc_info=True)


async def sync_commands(bot: commands.Bot) -> None:
    """Register slash commands with Discord (dev-guild scoped or global)."""
    dev_guild_id = get_dev_guild_id()
    if dev_guild_id:
        guild = discord.Object(id=dev_guild_id)
        synced = await bot.tree.sync(guild=guild)
        logger.info(f"Registered {len(synced)} slash command(s) for dev guild {dev_guild_id}.")
    else:
        synced = await bot.tree.sync()
        logger.info(f"Registered {len(synced)} slash command(s) globally.")


class CustomBot(commands.Bot):
    """Central bot class: holds shared services and cross-guild state."""

    def __init__(self, auto_sync: bool = True):
        super().__init__(
            command_prefix=os.getenv("BOT_PREFIX", "!"),
            intents=self._default_intents(),
            help_command=None,  # custom /help slash command
        )
        self._auto_sync = auto_sync
        # Shared chat API client, used by all cogs.
        self.llm = LLMClient()
        # Per-guild model override: {guild_id: model_id}
        self.guild_models: dict[int, str] = {}
        # Per-channel conversation memory:
        #   {channel_id: {"messages": [{"role", "content"}, ...], "ts": last_activity}}
        self.conversations: dict[int, dict] = {}

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

    def get_history(self, channel_id: int) -> list[dict]:
        """Prior turns for a channel, or [] if the conversation is stale/empty."""
        conv = self.conversations.get(channel_id)
        if not conv:
            return []
        if time.time() - conv["ts"] > HISTORY_TTL_SECONDS:
            self.conversations.pop(channel_id, None)
            return []
        return conv["messages"]

    def add_to_history(self, channel_id: int, role: str, content: str) -> None:
        """Remember one turn of a channel's conversation (trimmed to a max size)."""
        conv = self.conversations.setdefault(channel_id, {"messages": [], "ts": time.time()})
        conv["messages"].append({"role": role, "content": content})
        conv["ts"] = time.time()
        if len(conv["messages"]) > HISTORY_MAX_MESSAGES:
            del conv["messages"][: len(conv["messages"]) - HISTORY_MAX_MESSAGES]

    def clear_history(self, channel_id: int) -> None:
        self.conversations.pop(channel_id, None)

    async def setup_hook(self):
        """Load all cogs from the cogs directory before connecting."""
        await load_cogs(self)

    async def on_ready(self):
        """Triggered when the bot is connected and ready."""
        logger.info(f"Logged in as: {self.user.name} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        # Register slash commands once the application ID is available.
        if self._auto_sync:
            try:
                await sync_commands(self)
            except Exception as e:
                logger.error(f"Error syncing slash commands: {e}", exc_info=True)

        if self.is_closed():
            return  # e.g. update.py closed the connection right after syncing

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
        await ctx.send(f"Error: `{error}`")
