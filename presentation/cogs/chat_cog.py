import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from presentation.utils import split_message

logger = logging.getLogger("ChatCog")

# Messages shown when the chat API is unavailable (not a chat reply).
NO_API_CONFIGURED = (
    "Chat API is not configured. Add `CHAT_API_URL` to `.env` and restart the bot."
)
API_ERROR = "I couldn't reach my AI brain just now. Please try again in a moment!"


class ChatCog(commands.Cog):
    """Presentation: chat via @mentions, DMs, and the /chat & !chat commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _chat_reply(self, content: str, user_name: str, guild_id: int | None,
                          channel_id: int) -> str:
        """Generate a reply with conversation memory (falls back to an error message)."""
        reply = await self.bot.chat_service.chat(
            content,
            user_name,
            channel_id,
            model=self.bot.model_service.effective_model(guild_id),
        )
        if reply is None:
            logger.error("Chat API returned no reply.")
            return API_ERROR if self.bot.chat_service.provider.enabled else NO_API_CONFIGURED
        return reply

    @staticmethod
    async def _reply_in_chunks(text: str, send_first, send_rest) -> None:
        """Send a reply split into Discord-safe chunks (<2000 chars)."""
        chunks = split_message(text)
        if not chunks:
            return
        await send_first(chunks[0])
        for chunk in chunks[1:]:
            await send_rest(chunk)

    def _is_command(self, message: discord.Message) -> bool:
        """True if the message starts with the bot's prefix (a command, not chat)."""
        prefix = self.bot.command_prefix
        prefixes = [prefix] if isinstance(prefix, str) else list(prefix)
        return any(message.content.startswith(p) for p in prefixes)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Reply when mentioned in a channel or messaged in a DM."""
        if message.author.bot or message.author == self.bot.user:
            return
        if self._is_command(message):
            return  # let the prefix command system handle it

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
                message.channel.id,
            )

        await self._reply_in_chunks(
            reply,
            lambda c: message.reply(c, mention_author=False),
            lambda c: message.channel.send(c),
        )

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
            interaction.channel_id,
        )
        await self._reply_in_chunks(
            f"**You:** {message}\n**Bot:** {reply}",
            lambda c: interaction.followup.send(c),
            lambda c: interaction.followup.send(c),
        )

    @commands.command(name="chat", description="Prefix version of /chat.")
    async def chat_prefix(self, ctx: commands.Context, *, message: str):
        async with ctx.typing():
            reply = await self._chat_reply(
                message,
                ctx.author.display_name,
                ctx.guild.id if ctx.guild else None,
                ctx.channel.id,
            )
        await self._reply_in_chunks(
            reply,
            lambda c: ctx.reply(c),
            lambda c: ctx.channel.send(c),
        )

    @app_commands.command(name="clear", description="Reset the bot's memory for this conversation.")
    async def clear_command(self, interaction: discord.Interaction):
        self.bot.chat_service.clear(interaction.channel_id)
        await interaction.response.send_message("Conversation memory cleared. Starting fresh!")


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatCog(bot))
