import time

import discord
from discord.ext import commands


class GeneralCog(commands.Cog):
    """General utility commands: /ping, /about, /help."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @discord.slash_command(name="ping", description="Check the bot latency and responsiveness.")
    async def ping(self, ctx: discord.ApplicationContext):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Pong!",
            description=f"Bot Latency: **{latency_ms} ms**",
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.respond(embed=embed)

    def _help_embed(self, guild_id: int | None) -> discord.Embed:
        active_model = self.bot.model_service.effective_model(guild_id)
        embed = discord.Embed(
            title="Bot Help & Commands",
            description=(
                "A Discord chatbot powered by an AI API. "
                "Chat with it by mentioning it, DMing it, or using `/chat`."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="How to Chat",
            value="• **@Mention** — `@BotName hello!` in any channel.\n"
                  "• **Direct Message** — DM the bot to chat privately.\n"
                  "• **`/chat message:<text>`** — chat via slash command.",
            inline=False,
        )
        embed.add_field(
            name="Chat Commands",
            value="• `/chat` - Send a message to the bot\n"
                  "• `/clear` - Reset the bot's memory for this conversation\n"
                  "• `/ping` - Check bot latency\n"
                  "• `/about` - Bot stats, uptime, and active model\n"
                  "• `/help` - Show this guide",
            inline=False,
        )
        embed.add_field(
            name="Model Management",
            value="• `/model show` - Current model in this server\n"
                  "• `/model list` - All models available on the API\n"
                  "• `/model set model:<name>` - Switch this server's model (with autocomplete)\n"
                  "• `/model reset` - Back to the global default",
            inline=False,
        )
        embed.add_field(
            name="Voice",
            value="• `/voice join` - Join your voice channel and listen\n"
                  "• `/voice listen` / `/voice stop` - Ask a question out loud, get a spoken answer\n"
                  "• `/voice say text:<msg>` - Make the bot speak\n"
                  "• `/voice status` / `/voice leave` - Check or leave",
            inline=False,
        )
        embed.add_field(
            name="Currently Active",
            value=f"• Model: **`{active_model}`**\n"
                  f"• Chat API: {'connected' if self.bot.chat_service.provider.enabled else 'not configured (built-in replies disabled)'}",
            inline=False,
        )
        embed.set_footer(text="Tip: model settings are per-server and reset when the bot restarts.")
        return embed

    @discord.slash_command(name="help", description="Show a full guide to the bot: chat, commands, and model management.")
    async def help_command(self, ctx: discord.ApplicationContext):
        await ctx.respond(embed=self._help_embed(ctx.guild_id))

    @commands.command(name="help", description="Prefix version of /help.")
    async def help_prefix(self, ctx: commands.Context):
        await ctx.send(embed=self._help_embed(ctx.guild.id if ctx.guild else None))

    @discord.slash_command(name="about", description="Information about this bot.")
    async def about(self, ctx: discord.ApplicationContext):
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        embed = discord.Embed(
            title="About This Bot",
            description="A Discord Chatbot built with Python and `py-cord`, powered by an AI chat API.",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(len(self.bot.users)), inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Python Version", value="3.12", inline=True)
        embed.add_field(name="py-cord", value=discord.__version__, inline=True)
        embed.add_field(name="Active Model", value=f"`{self.bot.model_service.effective_model(ctx.guild_id)}`", inline=True)

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(GeneralCog(bot))
