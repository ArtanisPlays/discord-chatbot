import os
import sys
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DiscordBot")

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content for @mentions and chatting

class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=os.getenv("BOT_PREFIX", "!"),
            intents=intents,
            help_command=None  # We use custom /help slash command
        )

    async def setup_hook(self):
        """Loads all cogs from the cogs directory before the bot connects."""
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
        
        # Set a rich custom activity status
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


async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token or token.strip() == "your_bot_token_here":
        logger.error("DISCORD_TOKEN is missing or not set in .env file.")
        sys.exit(1)

    bot = CustomBot()
    try:
        async with bot:
            await bot.start(token)
    except discord.errors.PrivilegedIntentsRequired:
        logger.error(
            "\n"
            + "=" * 70 + "\n"
            + "⚠️ PRIVILEGED INTENT ERROR:\n"
            + "Your bot token is valid, but 'Message Content Intent' is not enabled in\n"
            + "the Discord Developer Portal.\n\n"
            + "TO FIX THIS IN 30 SECONDS:\n"
            + "1. Open https://discord.com/developers/applications/\n"
            + "2. Click on your Bot application\n"
            + "3. In the left menu, click 'Bot'\n"
            + "4. Scroll down to 'Privileged Gateway Intents'\n"
            + "5. Toggle ON 'Message Content Intent' (and 'Server Members Intent')\n"
            + "6. Click 'Save Changes' at the bottom\n"
            + "7. Re-run: python main.py\n"
            + "=" * 70
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down gracefully...")

