import asyncio
import logging

import discord
from discord.ext import commands

from infrastructure.voice_receiver import VoiceReceiver

logger = logging.getLogger("VoiceCog")


class VoiceCog(commands.Cog):
    """Presentation: voice channel join/leave, listening (STT), and speech (TTS)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.receiver = VoiceReceiver()
        self.listening: bool = False

    # ------------------------------------------------------------------ utils

    def _get_voice(self, guild_id: int | None):
        """The guild's active voice client, or None."""
        if guild_id is None:
            return None
        guild = self.bot.get_guild(guild_id)
        return guild.voice_client if guild else None

    def _is_same_channel(self, member: discord.Member, vc) -> bool:
        """True if `member` is in the same voice channel as the bot."""
        return (
            member.voice is not None
            and member.voice.channel is not None
            and vc is not None
            and vc.channel is not None
            and member.voice.channel.id == vc.channel.id
        )

    async def _play(self, vc, text: str) -> None:
        """Synthesize `text` and play it in the voice channel."""
        audio_path = await self.bot.voice_service.speak(text)
        if not audio_path:
            return
        if vc is None or not vc.is_connected():
            return
        if vc.is_playing():
            vc.stop()
        vc.play(discord.FFmpegPCMAudio(audio_path))

    async def _on_recording_done(self, paths: dict[int, str], guild_id: int | None,
                                 channel_id: int) -> None:
        """Transcribe recorded audio, chat, and reply with speech + text."""
        self.listening = False
        bot_id = self.bot.user.id if self.bot.user else None

        transcript = ""
        speaker_id = None
        for user_id, wav in paths.items():
            if user_id == bot_id:
                continue
            text = await self.bot.voice_service.transcribe(wav)
            if text:
                transcript = text
                speaker_id = user_id
                break

        if not transcript:
            logger.info("No speech recognized in the recording.")
            return

        vc = self._get_voice(guild_id)
        if vc is None or not vc.is_connected():
            return

        channel = self.bot.get_channel(channel_id) or vc.channel
        user_name = "user"
        if speaker_id is not None:
            member = vc.guild.get_member(speaker_id)
            user_name = member.display_name if member else "user"

        model = self.bot.model_service.effective_model(guild_id)
        reply = await self.bot.voice_service.handle_transcript(
            transcript, user_name, guild_id, channel_id, model=model
        )
        if not reply:
            reply = "Aku nggak bisa jawab sekarang, coba lagi ya."

        await self._play(vc, reply)

        try:
            if isinstance(channel, discord.TextChannel):
                await channel.send(
                    f"**{user_name}:** {transcript}\n**{self.bot.user.display_name}:** {reply}"
                )
        except Exception as e:
            logger.warning("Could not echo the voice exchange to text: %s", e)

    # ------------------------------------------------------------- commands

    voice_group = discord.SlashCommandGroup(
        name="voice", description="Voice channel controls for the bot."
    )

    @voice_group.command(name="join", description="Make the bot join your voice channel and listen.")
    async def voice_join(self, ctx: discord.ApplicationContext):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.respond("You are not in a voice channel. Join one first!", ephemeral=True)
            return
        vc = self._get_voice(ctx.guild_id)
        if vc is not None and vc.is_connected():
            await ctx.respond("I'm already in a voice channel.", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        await ctx.defer()
        try:
            vc = await channel.connect()
        except Exception as e:
            logger.error("Failed to connect to voice: %s", e)
            await ctx.respond(f"Could not join `{channel.name}`: {e}", ephemeral=True)
            return
        self.receiver.start(vc, self._on_recording_done, ctx.guild_id, ctx.channel_id)
        self.listening = True
        await ctx.respond(f"Joined **{channel.name}** and listening. Ask your question, then use `/voice stop`.")

    @voice_group.command(name="leave", description="Make the bot leave the voice channel.")
    async def voice_leave(self, ctx: discord.ApplicationContext):
        vc = self._get_voice(ctx.guild_id)
        if vc is None or not vc.is_connected():
            await ctx.respond("I'm not in a voice channel.", ephemeral=True)
            return
        if getattr(vc, "is_recording", lambda: False)():
            vc.stop_recording()
        self.listening = False
        await vc.disconnect()
        await ctx.respond("Left the voice channel.")

    @voice_group.command(name="status", description="Show the bot's voice channel status.")
    async def voice_status(self, ctx: discord.ApplicationContext):
        vc = self._get_voice(ctx.guild_id)
        if vc is None or not vc.is_connected():
            await ctx.respond("Not connected to any voice channel.")
            return
        members = [m.display_name for m in vc.channel.members if not m.bot]
        embed = discord.Embed(
            title="Voice Status",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Channel", value=f"`{vc.channel.name}`", inline=True)
        embed.add_field(name="Listening", value="yes" if self.listening else "no", inline=True)
        embed.add_field(name="Speaking", value="yes" if vc.is_playing() else "no", inline=True)
        embed.add_field(name="Members", value=", ".join(members) or "none", inline=False)
        await ctx.respond(embed=embed)

    @voice_group.command(name="listen", description="Start recording everyone in the voice channel.")
    async def voice_listen(self, ctx: discord.ApplicationContext):
        vc = self._get_voice(ctx.guild_id)
        if vc is None or not vc.is_connected():
            await ctx.respond("I'm not in a voice channel. Use `/voice join` first!", ephemeral=True)
            return
        if not self._is_same_channel(ctx.author, vc):
            await ctx.respond("You need to be in my voice channel to start listening.", ephemeral=True)
            return
        if self.listening:
            await ctx.respond("I'm already listening.", ephemeral=True)
            return
        self.receiver.start(vc, self._on_recording_done, ctx.guild_id, ctx.channel_id)
        self.listening = True
        await ctx.respond("Listening... ask your question, then use `/voice stop`.")

    @voice_group.command(name="stop", description="Stop listening and answer what was said.")
    async def voice_stop(self, ctx: discord.ApplicationContext):
        vc = self._get_voice(ctx.guild_id)
        if vc is None or not vc.is_connected():
            await ctx.respond("I'm not in a voice channel.", ephemeral=True)
            return
        if not getattr(vc, "is_recording", lambda: False)():
            await ctx.respond("I'm not listening right now. Use `/voice listen` first.", ephemeral=True)
            return
        await ctx.respond("Stopped listening. Let me think about your question...")
        vc.stop_recording()

    @voice_group.command(name="say", description="Make the bot speak a message out loud.")
    @discord.option("text", description="The message the bot should say")
    async def voice_say(self, ctx: discord.ApplicationContext, text: str):
        vc = self._get_voice(ctx.guild_id)
        if vc is None or not vc.is_connected():
            await ctx.respond("I'm not in a voice channel. Use `/voice join` first!", ephemeral=True)
            return
        await ctx.defer()
        await self._play(vc, text)
        await ctx.respond("Speaking...")


def setup(bot: commands.Bot):
    bot.add_cog(VoiceCog(bot))
