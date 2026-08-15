import re
import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

class ChatCog(commands.Cog):
    """Cog responsible for conversational interactions, mentions, DMs, and chat commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Sample conversational responses for prototype testing
        self.greetings = [
            "Hello there, {user}! 👋 How are you doing today?",
            "Hey {user}! Nice to hear from you. What's on your mind?",
            "Hi {user}! I'm all ears. What can I do for you?",
            "Greetings, {user}! Ready to chat whenever you are!"
        ]
        self.jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "There are only 10 types of people in the world: those who understand binary, and those who don't.",
            "Why was the JavaScript developer sad? Because they didn't Node how to Express themselves.",
            "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'"
        ]
        self.casual_replies = [
            "That's really interesting! Tell me more about it.",
            "I see what you mean! As a prototype bot, I'm constantly learning.",
            "Fascinating point! What do you think will happen next?",
            "I'm listening! Everything's running smoothly on my end.",
            "Haha, I like your perspective on that!",
            "Definitely! Feel free to ask me anything or test out my commands."
        ]

    def generate_reply(self, message_text: str, user_name: str) -> str:
        """Prototype rule-based response generator.
        (This function is structured so you can easily plug in an LLM API like Gemini/OpenAI).
        """
        clean_text = message_text.strip().lower()

        # Handle Empty message
        if not clean_text:
            return f"Hello {user_name}! You mentioned me, how can I help you today?"

        # Check for Greetings
        if re.search(r"\b(hi|hello|hey|greetings|howdy|sup|yo)\b", clean_text):
            return random.choice(self.greetings).format(user=user_name)

        # Check for How are you
        if "how are you" in clean_text or "how're you" in clean_text or "how do you do" in clean_text:
            return f"I'm doing fantastic, {user_name}! Thanks for asking. How are you doing today?"

        # Check for Who are you / what are you
        if "who are you" in clean_text or "what are you" in clean_text:
            return (
                f"I am a custom Discord chatbot prototype created for this server! "
                f"I can chat with you, respond to mentions, and run slash commands like `/ping` and `/help`."
            )

        # Check for Jokes
        if "joke" in clean_text or "funny" in clean_text:
            return f"Here is one for you:\n\n{random.choice(self.jokes)}"

        # Check for Dice / Coin flip
        if "roll" in clean_text and "dice" in clean_text:
            roll_result = random.randint(1, 6)
            return f"🎲 You rolled a **{roll_result}**!"
        if "flip" in clean_text and "coin" in clean_text:
            coin_result = random.choice(["Heads", "Tails"])
            return f"🪙 The coin landed on **{coin_result}**!"

        # Check for thanks / appreciation
        if re.search(r"\b(thank|thanks|thx|ty|appreciate)\b", clean_text):
            return f"You're very welcome, {user_name}! Always happy to help. 😊"

        # Check for bye / goodbye
        if re.search(r"\b(bye|goodbye|see ya|cya|catch you later)\b", clean_text):
            return f"Goodbye {user_name}! Have a wonderful rest of your day! 👋"

        # Default conversational response
        return random.choice(self.casual_replies)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listens for mentions and DMs to reply naturally in chat."""
        # Avoid replying to ourselves or other bots
        if message.author.bot or message.author == self.bot.user:
            return

        # Check if the bot was mentioned in a server channel or if message is in DM
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.bot.user in message.mentions

        if is_mentioned or is_dm:
            # Clean bot mentions out of the text
            clean_content = message.content
            if self.bot.user:
                clean_content = clean_content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "")
            clean_content = clean_content.strip()

            # Show typing indicator for realistic conversational feel
            async with message.channel.typing():
                await asyncio.sleep(0.6)  # Small brief delay to simulate thinking
                reply = self.generate_reply(clean_content, message.author.display_name)
                
            await message.reply(reply, mention_author=False)

    @app_commands.command(name="chat", description="Send a message to chat with the bot.")
    @app_commands.describe(message="The message or question you want to ask the bot")
    async def chat_command(self, interaction: discord.Interaction, message: str):
        """Slash command for chatting with the bot."""
        await interaction.response.defer()
        await asyncio.sleep(0.5)
        
        reply = self.generate_reply(message, interaction.user.display_name)
        await interaction.followup.send(f"💬 **You:** {message}\n🤖 **Bot:** {reply}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatCog(bot))
