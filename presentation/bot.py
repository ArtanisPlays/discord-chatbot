import os
import logging

import discord
from discord.ext import commands

from application.chat_service import ChatService
from application.model_service import ModelService
from infrastructure.config import get_dev_guild_id
from infrastructure.conversation_store import MemoryConversationStore
from infrastructure.llm_client import LLMClient

logger = logging.getLogger("DiscordBot")


async def load_cogs(bot: commands.Bot) -> None:
    """Load every cog from the presentation/cogs directory."""
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    if os.path.exists(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"presentation.cogs.{filename[:-3]}"
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


def create_bot(*, auto_sync: bool = True) -> "CustomBot":
    """Composition root: wire the infrastructure and application layers together."""
    llm = LLMClient()
    store = MemoryConversationStore()
    model_service = ModelService(llm)
    chat_service = ChatService(llm, store)
    return CustomBot(
        llm=llm,
        model_service=model_service,
        chat_service=chat_service,
        auto_sync=auto_sync,
    )


class CustomBot(commands.Bot):
    """Presentation entry point: owns Discord wiring and injected services."""

    def __init__(
        self,
        *,
        llm: LLMClient,
        model_service: ModelService,
        chat_service: ChatService,
        auto_sync: bool = True,
    ):
        super().__init__(
            command_prefix=os.getenv("BOT_PREFIX", "!"),
            intents=self._default_intents(),
            help_command=None,  # custom /help slash command
        )
        self._auto_sync = auto_sync
        self.llm = llm
        self.model_service = model_service
        self.chat_service = chat_service

    @staticmethod
    def _default_intents() -> discord.Intents:
        intents = discord.Intents.default()
        intents.message_content = True  # required to read message content
        return intents

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
