import asyncio
import logging

from dotenv import load_dotenv

from infrastructure.config import get_discord_token, setup_logging
from presentation.bot import create_bot, sync_commands

load_dotenv()

logger = logging.getLogger("Update")


async def main() -> None:
    """Register slash command changes with Discord, then exit."""
    bot = create_bot(auto_sync=False)

    @bot.listen()
    async def on_ready():
        try:
            await sync_commands(bot)
            logger.info("Done. Now run: python start.py")
        finally:
            await bot.close()

    await bot.start(get_discord_token())


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
