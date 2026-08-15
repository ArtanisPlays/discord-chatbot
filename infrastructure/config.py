import os
import sys
import logging


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_discord_token() -> str:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token or token == "your_bot_token_here":
        logging.getLogger("DiscordBot").error("DISCORD_TOKEN is missing or not set in .env file.")
        sys.exit(1)
    return token


def get_dev_guild_id() -> int | None:
    """The test server ID for instant command sync, or None for global sync."""
    raw = os.getenv("DEV_GUILD_ID", "").strip()
    return int(raw) if raw.isdigit() else None
