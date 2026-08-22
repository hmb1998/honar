# 👑 HMB • NEXUS

<div align="center">

## ⚡ ALL-IN-ONE DISCORD BOT

**Music • Moderation • Anti-Spam • Games • Economy • Fun • Utility • Images**

Built with ❤️ by **HONAR** for modern Discord communities.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.7.1-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Railway](https://img.shields.io/badge/Deploy-Railway-7B61FF?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app/)
[![YouTube](https://img.shields.io/badge/Music-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/)

</div>

---

## 🌌 What is HMB • NEXUS?

**HMB • NEXUS** is a professional all-in-one Discord bot designed to bring the most important server tools into one powerful system.

Instead of running separate bots for music, moderation, games, economy and utilities, NEXUS combines them into a single organized application with a custom **Music Control Panel**, HMB application emojis, slash commands and Railway-ready deployment.

> ⚡ **More than a bot. We are NEXUS.**

---

## ✨ Core Features

### 🎵 Music System
- `/play` with YouTube search or URL support
- 🎧 Voice playback with queue management
- ⏮️ Previous / ⏯️ Play-Pause / ⏭️ Skip / ⏹️ Stop
- 🔊 Volume control
- 🔀 Shuffle
- 📜 Lyrics support
- 📋 Queue management
- 🎛️ Custom HMB Music Control Panel
- 🔎 Search directly from the music panel
- 🔁 Multiple YouTube extraction/fallback strategies
- 🍪 Current Railway version is designed to work **without `YOUTUBE_COOKIE`**

### 🛡️ Moderation
- Warn / kick / ban tools
- Server moderation utilities
- Member management
- Voice moderation tools
- Server protection helpers

### 🚨 Anti-Spam
- Anti-spam protection
- Automated message filtering helpers
- Community safety utilities

### 🎮 Games & Fun
- Interactive games
- Fun commands
- Entertainment features for community servers

### 💰 Economy
- Economy features for active communities
- User-focused server interaction tools

### 🧰 Utility & Information
- Server information
- User information
- Utility commands
- Helpful community tools

### 🖼️ Images
- Image-related commands and utilities

### 🐙 GitHub Integration
- GitHub-focused utility commands through the dedicated GitHub cog

### 👑 HMB NEXUS System
- Custom HMB application emojis
- Automatic server emoji synchronization
- HMB branding throughout the bot
- Custom presence
- Modular Cog architecture

---

## 🎛️ HMB Music Control Panel

NEXUS includes a custom music interface for controlling playback without relying only on commands.

**Available controls:**

`Previous` • `Play / Pause` • `Skip` • `Stop` • `Queue` • `Volume` • `Shuffle` • `Lyrics` • `Search`

The Search button uses the same music resolver as `/play`, so users can search for a song by name or paste a YouTube link.

---

## 🧩 Project Structure

```text
HMB-NEXUS/
├── main.py                 # Bot entry point
├── config.py               # Environment/configuration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Railway/Docker deployment
├── web_server.py           # Web/health server
│
├── cogs/
│   ├── admin.py             # Administration
│   ├── moderation.py        # Moderation
│   ├── antispam.py          # Anti-spam
│   ├── fun.py               # Fun commands
│   ├── utility.py           # Utilities
│   ├── info.py              # Information commands
│   ├── economy.py           # Economy
│   ├── games.py             # Games
│   ├── images.py            # Image tools
│   ├── music.py             # Music engine
│   ├── music_panel.py       # Music Control Panel
│   ├── github.py             # GitHub tools
│   └── hmb.py                # HMB features
│
├── media/                   # Bot media/assets
├── rich_presence/           # Rich Presence helpers
├── privacy.html             # Privacy Policy
├── terms.html               # Terms of Service
└── README.md                # Project documentation
```

The current entry point loads **13 modular Cogs**, keeping the bot organized and easier to maintain.

---

## 🛠️ Technology

| Technology | Purpose |
|---|---|
| 🐍 Python 3.13+ | Main runtime |
| 🤖 discord.py 2.7.1 | Discord API / Bot framework |
| 🎵 yt-dlp | YouTube media extraction |
| 🧩 yt-dlp-ejs | YouTube JavaScript challenge support |
| 🔐 BgUtils PO-token provider | YouTube anti-bot assistance |
| 🔊 PyNaCl | Discord voice support |
| 🌐 aiohttp | HTTP/network operations |
| 🖼️ Pillow | Image processing |
| 🐳 Docker | Container deployment |
| 🚂 Railway | Production hosting |

---

## 🚂 Railway Deployment

HMB • NEXUS is prepared for Railway using the included `Dockerfile`.

### Required variable

```env
DISCORD_TOKEN=your_bot_token
```

### YouTube Cookie

> 🍪 **Do not add `YOUTUBE_COOKIE` for the current no-cookie build.**

The current music implementation includes several extraction/fallback mechanisms. YouTube can change its anti-bot and playback requirements, so no third-party extractor can guarantee permanent playback for every video or every hosting IP.

### Deploy steps

1. Push the latest code to GitHub.
2. Connect the repository to Railway.
3. Make sure `DISCORD_TOKEN` is configured.
4. Deploy using the included `Dockerfile`.
5. Open **Deploy Logs**.
6. Confirm the bot logs in successfully.
7. Test `/play <song name>`.
8. Open the HMB Music Panel and test **Search**.

---

## 🔐 Security

**Never commit secrets to GitHub.**

Do not place these in source files or README files:

```text
DISCORD_TOKEN
Bot tokens
API keys
Private credentials
Session cookies
```

Use Railway Variables / environment variables instead.

---

## 🧪 Troubleshooting Music

If YouTube playback fails:

1. Check Railway **Deploy Logs**.
2. Confirm the bot is connected to the voice channel.
3. Test a normal YouTube URL with `/play`.
4. Test the Music Panel **Search** button.
5. Make sure the latest deployment is active.
6. Check whether YouTube is returning an anti-bot/403 response.

A successful download reaching `100%` confirms that the media extraction/download stage completed; a later FFmpeg/voice error is a separate playback-stage problem.

---

## 📊 Current Architecture

```text
Discord
   │
   ▼
HMB • NEXUS
   │
   ├── Slash Commands
   ├── HMB Application Emojis
   ├── Music Control Panel
   │      ├── Search
   │      ├── Queue
   │      ├── Playback Controls
   │      └── Lyrics
   │
   ├── Music Resolver
   │      ├── yt-dlp
   │      ├── EJS support
   │      ├── PO-token provider
   │      └── Public fallback
   │
   └── Modular Cogs
          ├── Admin
          ├── Moderation
          ├── Anti-Spam
          ├── Games
          ├── Economy
          ├── Fun
          ├── Utility
          ├── Info
          ├── Images
          ├── GitHub
          └── HMB
```

---

## 👑 About HONAR

HMB • NEXUS is built and maintained by **HONAR** with a focus on a fast, clean and professional Discord experience.

**HMB • NEXUS — More than a bot. We are NEXUS.**

---

## 📜 Legal

- **Terms of Service:** `terms.html`
- **Privacy Policy:** `privacy.html`

---

<div align="center">

### ⚡ HMB • NEXUS
**Powered by HONAR 👑**

</div>
