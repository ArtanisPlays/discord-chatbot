import time

import discord
from discord import app_commands
from discord.ext import commands


class GeneralCog(commands.Cog):
    """General utility commands: /ping, /about, /help."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="ping", description="Check the bot latency and responsiveness.")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title=" Pong!",
            description=f"Bot Latency: **{latency_ms} ms**",
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Show a full guide to the bot: chat, commands, and model management.")
    async def help_command(self, interaction: discord.Interaction):
        active_model = self.bot.effective_model(interaction.guild_id)
        embed = discord.Embed(
            title="🤖 Bot Help & Commands",
            description=(
                "A Discord chatbot powered by an AI API. "
                "Chat with it by mentioning it, DMing it, or using `/chat`."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="💬 How to Chat",
            value="• **@Mention** — `@BotName hello!` in any channel.\n"
                  "• **Direct Message** — DM the bot to chat privately.\n"
                  "• **`/chat message:<text>`** — chat via slash command.",
            inline=False,
        )
        embed.add_field(
            name="🤖 Chat Commands",
            value="• `/chat` - Send a message to the bot\n"
                  "• `/ping` - Check bot latency\n"
                  "• `/about` - Bot stats, uptime, and active model\n"
                  "• `/help` - Show this guide",
            inline=False,
        )
        embed.add_field(
            name="🧠 Model Management",
            value="• `/model show` - Current model in this server\n"
                  "• `/model list` - All models available on the API\n"
                  "• `/model set model:<name>` - Switch this server's model (with autocomplete)\n"
                  "• `/model reset` - Back to the global default",
            inline=False,
        )
        embed.add_field(
            name="⚙️ Currently Active",
            value=f"• Model: **`{active_model}`**\n"
                  f"• Chat API: {'connected' if self.bot.llm.enabled else 'not configured (built-in replies disabled)'}",
            inline=False,
        )
        embed.set_footer(text="Tip: model settings are per-server and reset when the bot restarts.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="about", description="Information about this bot.")
    async def about(self, interaction: discord.Interaction):
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        embed = discord.Embed(
            title="ℹ️ About This Bot",
            description="A Discord Chatbot built with Python and `discord.py`, powered by an AI chat API.",
            color=discord.Color.blue(),
        )
        embed.add_field(name="🌐 Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Users", value=str(len(self.bot.users)), inline=True)
        embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="🐍 Python Version", value="3.12", inline=True)
        embed.add_field(name="📦 discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="🧠 Active Model", value=f"`{self.bot.effective_model(interaction.guild_id)}`", inline=True)

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
