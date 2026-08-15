import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("ChatCog")

# Messages shown when the chat API is unavailable (not a chat reply).
NO_API_CONFIGURED = (
    "⚠️ Chat API is not configured. Add `CHAT_API_URL` to `.env` and restart the bot."
)
API_ERROR = "😵 I couldn't reach my AI brain just now. Please try again in a moment!"


class ChatCog(commands.Cog):
    """Handles chat: @mentions, DMs, and the /chat slash command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _chat_reply(self, content: str, user_name: str, guild_id: int | None) -> str:
        """Generate a reply from the chat API (falls back to an error message)."""
        if not self.bot.llm.enabled:
            logger.warning("Chat API is not configured; cannot reply.")
            return NO_API_CONFIGURED

        reply = await self.bot.llm.generate_reply(
            content,
            user_name,
            model=self.bot.effective_model(guild_id),
        )
        if not reply:
            logger.error("Chat API returned no reply.")
            return API_ERROR
        return reply

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Reply when mentioned in a channel or messaged in a DM."""
        if message.author.bot or message.author == self.bot.user:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.bot.user in message.mentions
        if not (is_mentioned or is_dm):
            return

        content = self._clean_mentions(message.content)
        if not content:
            content = "Hello!"

        async with message.channel.typing():
            reply = await self._chat_reply(
                content,
                message.author.display_name,
                message.guild.id if message.guild else None,
            )

        await message.reply(reply, mention_author=False)

    def _clean_mentions(self, text: str) -> str:
        """Strip the bot's own <@id> / <@!id> mentions from a message."""
        if self.bot.user:
            text = text.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "")
        return text.strip()

    @app_commands.command(name="chat", description="Send a message to chat with the bot.")
    @app_commands.describe(message="The message or question you want to ask the bot")
    async def chat_command(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        await asyncio.sleep(0.5)

        reply = await self._chat_reply(
            message,
            interaction.user.display_name,
            interaction.guild_id,
        )
        await interaction.followup.send(f"💬 **You:** {message}\n🤖 **Bot:** {reply}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatCog(bot))
