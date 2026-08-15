# 🤖 Custom Discord Chatbot Prototype

A custom Discord chatbot built in Python using **`discord.py` (v2.x)** with modern slash commands (`app_commands`), interactive conversational replies on `@mentions` and direct messages (DMs), and modular cog architecture.

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
python main.py
```

You should see:
```text
[INFO] DiscordBot: Loaded cog extension: cogs.general
[INFO] DiscordBot: Loaded cog extension: cogs.chat
[INFO] DiscordBot: Syncing slash commands...
[INFO] DiscordBot: Successfully synced 4 slash command(s) globally.
[INFO] DiscordBot: 🤖 Logged in as: YourBotName (ID: ...)
[INFO] DiscordBot: 🌐 Connected to X guild(s)
```

---

## 💬 How to Interact With the Bot

| Feature / Command | How to Use | Description |
| :--- | :--- | :--- |
| **@Mention Chat** | `@BotName Hello!` | Replies with AI-generated responses (using the configured chat API). |
| **DM Chat** | Direct Message | Send a private message directly to the bot anytime. |
| **`/chat`** | `/chat message:How's the weather?` | Slash command interface for chatting with the bot. |
| **`/ping`** | `/ping` | Displays current bot latency (in milliseconds). |
| **`/about`** | `/about` | Displays system status, uptime, server count, library versions, and active model. |
| **`/help`** | `/help` | Shows a full guide: how to chat, all commands, and model management. |
| **`/model show`** | `/model show` | Shows the chat model currently active in the server. |
| **`/model list`** | `/model list` | Lists every model available on the chat API. |
| **`/model set`** | `/model set model:<name>` | Switches the server's chat model (with autocomplete from the API). |
| **`/model reset`** | `/model reset` | Reverts the server's model to the global default. |

Model selection is per-server (each Discord server can pick its own model). The choice is kept in memory and resets to the global default (`CHAT_API_MODEL`) whenever the bot restarts.

---

## 📁 Project Structure

```text
Chatbot/
├── .env                   # Stores your private DISCORD_TOKEN and CHAT_API_* keys
├── .env.example           # Template for environment variables
├── .gitignore             # Keeps secrets and cache out of version control
├── main.py                # Entry point: logging, token check, starts the bot
├── bot.py                 # CustomBot: intents, shared LLM client, guild model state
├── requirements.txt       # Python dependencies (discord.py, python-dotenv, aiohttp)
├── README.md              # Setup and usage documentation
├── services/
│   └── llm_client.py      # Async chat API client (OpenAI-compatible, SSE streaming)
└── cogs/
    ├── chat.py            # @mentions, DMs, and /chat (AI replies only)
    ├── general.py         # Slash commands: /ping, /help, /about
    └── models.py          # /model show, list, set, reset
```

---

## 🧠 Connecting a Real AI (LLM API)
The bot replies using an AI chat API endpoint. Set these variables in your `.env` file (OpenAI-compatible format, so it works with OpenAI, OpenRouter, Groq, Together, Gemini OpenAI-compat mode, or local servers like Ollama / llama.cpp / LM Studio / vLLM):

```env
CHAT_API_URL=https://api.openai.com/v1/chat/completions   # your endpoint
CHAT_API_KEY=sk-xxxx                                      # leave empty for local servers
CHAT_API_MODEL=gpt-4o-mini                                # model name
CHAT_API_SYSTEM_PROMPT=You are a friendly Discord chatbot.
CHAT_API_TIMEOUT=30                                       # seconds
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

Example with Gemini via OpenAI-compatible endpoint:
```env
CHAT_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
CHAT_API_KEY=YOUR_GEMINI_API_KEY
CHAT_API_MODEL=gemini-2.0-flash
```
