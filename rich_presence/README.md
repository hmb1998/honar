# HMB NEXUS — Local Rich Presence Companion

This is separate from the Railway bot.

Discord's official RPC `SET_ACTIVITY` updates the Rich Presence of the **Discord desktop user running this companion**. It does not turn a bot Gateway presence into a Rich Presence with art assets.

## 1. Requirements

- Discord Desktop must be running.
- Run this companion on the same computer as Discord Desktop.
- The Discord application ID is already set to HMB NEXUS.

## 2. Asset keys

In Discord Developer Portal → Rich Presence → Art Assets, upload your 1024×1024 images and use the exact asset keys shown by Discord. Asset keys are lowercase.

Create environment variables before starting:

```text
DISCORD_APPLICATION_ID=1540575563607969832
HMB_LARGE_IMAGE_KEY=your_large_asset_key
HMB_SMALL_IMAGE_KEY=your_small_asset_key
HMB_RP_DETAILS=HMB NEXUS • Discord Bot
HMB_RP_STATE=Music • Moderation • Games • Economy
HMB_RP_LARGE_TEXT=HMB • NEXUS
HMB_RP_SMALL_TEXT=Online
HMB_RP_PARTY_ID=HMB-NEXUS
HMB_RP_PARTY_SIZE=1
HMB_RP_PARTY_MAX=5
```

Optional button:

```text
HMB_RP_BUTTON_URL=https://discord.com/invite/your-server
```

## 3. Start

From this directory:

```bash
python run_presence.py
```

The companion reconnects only when restarted; keep it running while you want the local Rich Presence active.

## Official Discord behavior

Discord documents `SET_ACTIVITY` as the RPC command for updating a user's Rich Presence. Rich Presence supports details, state, timestamps, party information and uploaded assets. Application/Activity assets are not the same thing as a bot Gateway presence.
