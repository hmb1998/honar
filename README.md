# HMB NEXUS — Railway Bot

## What is active on Railway

- Discord Gateway bot: **YES**
- 10 Discord Application Emojis: **YES**
- Slash commands: **YES**
- Bot Gateway presence: **YES**
- Rich Presence portal assets: **uploaded/configured**, but they are not attached to a bot Gateway presence.

## Railway Variables

You do **not** need a `.env` file on Railway. Add these variables in Railway → Variables:

```text
DISCORD_TOKEN=your_bot_token
GITHUB_TOKEN=your_github_token_optional
DISCORD_APPLICATION_ID=1540575563607969832
HMB_PRESENCE_NAME=HMB • NEXUS
HMB_PRESENCE_STATE=Music • Moderation • Games • Economy
```

`DISCORD_TOKEN` is required. Never put the bot token directly into source code.

## Verify the 10 application emojis

After deployment, use:

```text
/hmb_emojis
```

The command displays all 10 application emojis and the footer reports `10/10` when all are available.

Use:

```text
/hmb_status
```

to verify the bot, emojis, slash commands and Gateway presence.

## Important: Rich Presence vs Bot Presence

Discord's documented Rich Presence RPC updates the **Discord user** running the local Discord Desktop client. It is not a mechanism for attaching Rich Presence art assets to a bot user's Gateway presence.

Therefore:

- Railway can keep the HMB bot online and set its normal Gateway presence.
- Your uploaded Rich Presence assets can be used by a supported Activity/SDK/RPC integration.
- A local Rich Presence companion must run on the same computer as Discord Desktop if you want the user's profile to show the large/small Rich Presence artwork through local RPC.

See `rich_presence/README.md` for the local companion.


## Make the 10 HMB emojis appear in the Discord Emoji Picker

Application Emojis are different from normal Server Custom Emojis. The
bot now includes a safe sync system that copies the 10 Application Emojis
into the target server.

Recommended Railway variable:

```text
HMB_EMOJI_GUILD_ID=YOUR_DISCORD_SERVER_ID
```

If the bot is in exactly one server, this variable can be left empty and
that server is selected automatically.

The bot needs **Manage Expressions** (Manage Emojis and Stickers).

You can also run:

```text
/hmb_sync_emojis
```

The command is restricted to users with **Manage Expressions**.

The server emoji names are:

```text
hmb_01
hmb_02
hmb_03
hmb_04
hmb_05
hmb_06
hmb_07
hmb_08
hmb_09
hmb_10
```

The startup sync does not create duplicates: if an emoji with the same
name already exists, it is left alone.
