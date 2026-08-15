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
| **@Mention Chat** | `@BotName Hello!` | Responds dynamically with conversation, jokes, dice rolls, coin flips, or greetings. |
| **DM Chat** | Direct Message | Send a private message directly to the bot anytime. |
| **`/chat`** | `/chat message:How's the weather?` | Slash command interface for chatting with the bot. |
| **`/ping`** | `/ping` | Displays current bot latency (in milliseconds). |
| **`/about`** | `/about` | Displays system status, uptime, server count, and library versions. |
| **`/help`** | `/help` | Shows an overview of bot commands and interaction methods. |

---

## 📁 Project Structure

```text
Chatbot/
├── .env                # Stores your private DISCORD_TOKEN
├── .env.example        # Template for environment variables
├── .gitignore          # Keeps secrets and cache out of version control
├── main.py             # Core bot initialization and cog loader
├── requirements.txt    # Python dependencies (discord.py, python-dotenv)
├── README.md           # Setup and usage documentation
└── cogs/
    ├── chat.py         # Handles @mentions, DMs, /chat, and conversational logic
    └── general.py      # Slash commands: /ping, /help, /about
```

---

## 🧠 Upgrading to LLM AI Chat (Gemini / OpenAI)
The chatting logic in [`cogs/chat.py`](file:///c:/Users/plays/Documents/Projects/Funny%20prokects/Discord%20Bot/Chatbot/cogs/chat.py) is modularized in `generate_reply()`. Whenever you are ready to connect a large language model (e.g. Gemini 1.5/2.0 or OpenAI GPT-4o), you can simply connect the API inside `generate_reply()` or `on_message` with memory context.
