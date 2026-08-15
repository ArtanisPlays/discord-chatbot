import time
import discord
from discord import app_commands
from discord.ext import commands

class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="ping", description="Check the bot latency and responsiveness.")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title=" Pong!",
            description=f"Bot Latency: **{latency_ms} ms**",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Show information about available commands and chatting.")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Bot Commands & Features",
            description="Welcome! Here is how you can interact with me:",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="💬 How to Chat",
            value="• **Mention me**: Simply `@mention` me in any server channel.\n"
                  "• **Direct Messages**: Send me a DM directly to chat privately.\n"
                  "• **/chat [message]**: Use the slash command to send a message.\n"
                  "• **/talk_mode**: Toggle or test different conversational response styles.",
            inline=False
        )
        embed.add_field(
            name="⚙️ Slash Commands",
            value="• `/ping` - Check bot latency\n"
                  "• `/about` - View bot statistics and info\n"
                  "• `/chat` - Chat directly with the bot\n"
                  "• `/help` - Show this guide",
            inline=False
        )
        embed.set_footer(text="Discord Bot Prototype")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="about", description="Information about this bot.")
    async def about(self, interaction: discord.Interaction):
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        embed = discord.Embed(
            title="ℹ️ About This Bot",
            description="A prototype Discord Chatbot built with Python and `discord.py`.",
            color=discord.Color.blue()
        )
        embed.add_field(name="🌐 Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Users", value=str(len(self.bot.users)), inline=True)
        embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="🐍 Python Version", value="3.12", inline=True)
        embed.add_field(name="📦 discord.py", value=discord.__version__, inline=True)

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
