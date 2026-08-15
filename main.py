import sys
import asyncio
import logging

import discord
from dotenv import load_dotenv

from bot import CustomBot
from config import get_discord_token, setup_logging

load_dotenv()

logger = logging.getLogger("DiscordBot")


async def run() -> None:
    bot = CustomBot()
    try:
        async with bot:
            await bot.start(get_discord_token())
    except discord.errors.PrivilegedIntentsRequired:
        logger.error(
            "\n"
            + "=" * 70 + "\n"
            + "PRIVILEGED INTENT ERROR:\n"
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


def main() -> None:
    setup_logging()
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Bot shutting down gracefully...")


if __name__ == "__main__":
    main()
