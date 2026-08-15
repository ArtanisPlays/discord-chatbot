# 🤖 Custom Discord Chatbot Prototype

A custom Discord chatbot built in Python using **py-cord (v2.x)** with modern slash commands, interactive conversational replies on `@mentions` and direct messages (DMs), modular cog architecture, and voice support (listens with speech-to-text and answers with text-to-speech).

---

## 🚀 Quick Setup & How to Run

### 1. Enable Privileged Gateway Intents (Required)
Before running the bot, ensure the following settings are enabled in the [Discord Developer Portal](https://discord.com/developers/applications):
1. Go to your application and select **Bot** from the left sidebar.
2. Scroll down to **Privileged Gateway Intents**.
3. Toggle **ON**:
   - ✅ **Message Content Intent** (Required for the bot to read messages and reply to `@mentions`)
   - ✅ **Server Members Intent** (Recommended)
4. Click **Save Changes**.

---

### 2. Invite the Bot to Your Server
To invite your bot with the required permissions and slash command access, use this pre-configured OAuth2 invite link:

👉 **[Invite Your Bot to Discord Server](https://discord.com/oauth2/authorize?client_id=1538142970417774612&permissions=277025778752&scope=bot%20applications.commands)**

*Or generate your own:*
1. Developer Portal ➔ **OAuth2** ➔ **URL Generator**.
2. Select scopes: `bot` and `applications.commands`.
3. Select bot permissions: `Send Messages`, `Read Message History`, `Embed Links`, `Attach Files`, `View Channels`, `Use Slash Commands`.

---

### 3. Run the Bot
Dependencies have already been installed. To start the bot:

```powershell
python start.py
```

> Alternatively `python main.py` does the same thing. Use `python update.py` after changing slash commands to re-register them with Discord instantly (see below).

You should see:
```text
[INFO] DiscordBot: Loaded cog extension: cogs.general
[INFO] DiscordBot: Loaded cog extension: cogs.chat
[INFO] DiscordBot: Loaded cog extension: cogs.models
[INFO] DiscordBot: Registered N slash command(s) for dev guild ...
[INFO] DiscordBot: Logged in as: YourBotName (ID: ...)
[INFO] DiscordBot: Connected to X guild(s)
```

---

## 🔄 Updating Slash Commands

After changing, adding, or removing slash commands, register them without running the bot:

```powershell
python update.py
python start.py
```

- `update.py` — logs in, loads cogs, and syncs the command tree (instant to `DEV_GUILD_ID` if set, otherwise global), then exits.
- `start.py` — runs the bot normally.

---

## 💬 How to Interact With the Bot

| Feature / Command | How to Use | Description |
| :--- | :--- | :--- |
| **@Mention Chat** | `@BotName Hello!` | Replies with AI-generated responses (using the configured chat API). |
| **DM Chat** | Direct Message | Send a private message directly to the bot anytime. |
| **`/chat`** | `/chat message:How's the weather?` | Slash command interface for chatting with the bot. |
| **`/clear`** | `/clear` | Resets the bot's memory for this conversation (starts a fresh topic). |
| **`/ping`** | `/ping` | Displays current bot latency (in milliseconds). |
| **`/about`** | `/about` | Displays system status, uptime, server count, library versions, and active model. |
| **`/help`** | `/help` | Shows a full guide: how to chat, all commands, and model management. |
| **`/model show`** | `/model show` | Shows the chat model currently active in the server. |
| **`/model list`** | `/model list` | Lists every model available on the chat API. |
| **`/model set`** | `/model set model:<name>` | Switches the server's chat model (with autocomplete from the API). |
| **`/model reset`** | `/model reset` | Reverts the server's model to the global default. |
| **`/voice join`** | `/voice join` | Bot joins your voice channel and starts listening. |
| **`/voice listen`** | `/voice listen` | Start recording everyone in the voice channel. |
| **`/voice stop`** | `/voice stop` | Stop listening and answer what was said (spoken + echoed in text). |
| **`/voice say`** | `/voice say text:<msg>` | Make the bot speak a message out loud (no listening). |
| **`/voice status`** | `/voice status` | Show channel, listening/speaking state, and members. |
| **`/voice leave`** | `/voice leave` | Bot leaves the voice channel. |

Prefix commands also work: **`!help`** and **`!chat <message>`**.

> **Tip (dev):** set `DEV_GUILD_ID` to your test server's ID to sync slash commands *instantly* to that server. Without it, commands sync globally, which can take up to ~1 hour to propagate (this is what causes Discord's "This command is outdated, please try again in a few minutes" message right after an update — restarting the Discord client also fixes it).

Model selection is per-server (each Discord server can pick its own model). The choice is kept in memory and resets to the global default (`CHAT_API_MODEL`) whenever the bot restarts.

The bot **remembers the conversation per channel** (mentions, DMs, and `/chat` all share the same memory), so you can have a real back-and-forth: it keeps the last `CHAT_HISTORY_MESSAGES` turns (default 20) and forgets everything after `CHAT_HISTORY_TTL` seconds of inactivity (default 1800s / 30 min). Use `/clear` to reset a conversation manually.

### 🎙️ Voice (listening + speaking)

The bot can talk **and** listen in voice channels, all with free, no-API-key services:

- **TTS (speaking)** — `edge-tts` uses Microsoft Edge's free online voices. Default voice `id-ID-GadisNeural` (Indonesian female). Audio is cached on disk so repeated messages don't re-synthesize.
- **STT (listening)** — `faster-whisper` runs Whisper locally (offline). The model (default `small`, ~460 MB) downloads once on first use. Indonesian language hint is set by default.
- **ffmpeg** — required to decode TTS MP3 into the PCM stream Discord accepts. Install with `winget install ffmpeg`.

**Flow:** `/voice join` → the bot listens → ask your question out loud → `/voice stop` → the bot transcribes it, sends it through the same chat pipeline (with conversation memory), then plays the answer and echoes the exchange in text.

> **Known limitation:** py-cord's voice *receiving* (listening) can fail on some servers because of Discord's DAVE end-to-end encryption rollout. If recordings come back garbled or empty, `/voice say` (speaking only) still works — the bot just won't be able to hear you. Set `STT_MODEL` to `base` for a smaller/faster model, or `medium` for better accuracy.

---

## 📁 Project Structure

```text
Chatbot/
├── .env                   # Stores your private DISCORD_TOKEN and CHAT_API_* keys
├── .env.example           # Template for environment variables
├── .gitignore             # Keeps secrets and cache out of version control
├── main.py                # Entry point: logging, token check, starts the bot
├── start.py               # Run the bot (same as main.py)
├── update.py              # Register/sync slash command changes, then exit
├── requirements.txt       # Python dependencies (py-cord, edge-tts, faster-whisper, ...)
├── README.md              # Setup and usage documentation
│
├── domain/                # Domain layer: pure business objects & contracts (no deps)
│   ├── models.py          # ChatMessage, Conversation
│   └── ports.py           # LLMProvider, ConversationStore, TTSProvider, STTProvider
├── application/           # Application layer: use cases / services
│   ├── chat_service.py    # ChatService: one turn + conversation memory
│   ├── model_service.py   # ModelService: model list cache + per-guild overrides
│   └── voice_service.py   # VoiceService: STT → chat → TTS pipeline
├── infrastructure/        # Infrastructure layer: adapters & I/O
│   ├── config.py          # Env config: logging setup, token & dev guild helpers
│   ├── llm_client.py      # LLMClient: OpenAI-compatible chat API (SSE streaming)
│   ├── conversation_store.py  # MemoryConversationStore: in-memory per-channel memory
│   ├── tts_client.py      # EdgeTTSClient: edge-tts synthesis + on-disk cache
│   ├── stt_client.py      # WhisperSTTClient: local faster-whisper transcription
│   └── voice_receiver.py  # VoiceReceiver: py-cord WaveSink recording → WAV files
└── presentation/          # Presentation layer: Discord interface
    ├── bot.py             # create_bot (composition root), CustomBot, cog loading/sync
    ├── utils.py           # split_message (Discord 2000-char safe chunking)
    └── cogs/
        ├── chat_cog.py    # @mentions, DMs, /chat, !chat, /clear
        ├── general_cog.py # /ping, /help, /about
        ├── models_cog.py  # /model show, list, set, reset
        └── voice_cog.py   # /voice join, listen, stop, say, status, leave
```

### Layered architecture

Dependencies flow one way: `presentation -> application -> domain` and `infrastructure -> domain`. The presentation layer talks to the domain through application services (`ChatService`, `ModelService`, `VoiceService`), and adapters in `infrastructure` implement the `domain.ports` contracts (`LLMProvider`, `ConversationStore`, `TTSProvider`, `STTProvider`), so swapping the LLM API, the memory store, or the voice engines never touches the cogs.

---

## 🧠 Connecting a Real AI (LLM API)
The bot replies using an AI chat API endpoint. Set these variables in your `.env` file (OpenAI-compatible format, so it works with OpenAI, OpenRouter, Groq, Together, Gemini OpenAI-compat mode, or local servers like Ollama / llama.cpp / LM Studio / vLLM):

```env
CHAT_API_URL=https://api.openai.com/v1/chat/completions   # your endpoint
CHAT_API_KEY=sk-xxxx                                      # leave empty for local servers
CHAT_API_MODEL=gpt-4o-mini                                # model name
CHAT_API_SYSTEM_PROMPT=Kamu adalah Garappizza, AI yang santai, ramah, dan asyik buat diajak ngobrol. Namamu adalah Garappizza. Jika ditanya "who are you?", "siapa kamu?", atau seputar identitasmu, selalu jawab dan perkenalkan dirimu sebagai Garappizza. Selalu gunakan bahasa yang sama dengan user. Jawab dengan gaya santai, natural, dan hangat seperti ngobrol sama teman, serta tetap ringkas dan tidak bertele-tele.
CHAT_API_TIMEOUT=120                                      # max idle (no-data) seconds before cancelling; slow streams are allowed
CHAT_HISTORY_MESSAGES=20                                  # turns of memory kept per channel
CHAT_HISTORY_TTL=1800                                     # idle seconds before memory resets
```

- The bot needs a configured API to reply. If `CHAT_API_URL` is empty or a request fails, the bot replies with a short error message instead of crashing.

Example with a local Ollama server:
```env
CHAT_API_URL=http://localhost:11434/v1/chat/completions
CHAT_API_MODEL=llama3.2
```

Example with the ragita.net endpoint (streaming SSE — works without `stream: false` support):
```env
CHAT_API_URL=https://chat.ragita.net/api/chat/completions
CHAT_API_KEY=eyJ...your_bearer_token
CHAT_API_MODEL=gpt-oss:20b
```

The client sends `"stream": true` and consumes the Server-Sent Events response, skipping reasoning/thinking chunks (`delta.reasoning_content`) and keeping only the final answer text (`delta.content`).

Slow responses are **not** cancelled: there is no overall request timeout. The request only gives up if the API goes silent for `CHAT_API_TIMEOUT` seconds (default 120s) — so a model that takes a while to "think" before streaming works fine.

Long replies are automatically split into multiple Discord-safe messages (max ~2000 chars each), breaking at paragraphs/lines/sentences and keeping markdown code blocks intact across chunks.

Example with Gemini via OpenAI-compatible endpoint:
```env
CHAT_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
CHAT_API_KEY=YOUR_GEMINI_API_KEY
CHAT_API_MODEL=gemini-2.0-flash
```
