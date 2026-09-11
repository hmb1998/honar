# HMB NEXUS — PostgreSQL + Render

## Recommended production setup

HMB NEXUS uses PostgreSQL for persistent Economy data when `DATABASE_URL` is configured.

Stored persistently:
- balance
- bank
- XP
- level
- inventory
- daily claim date

Temporary music files are cleaned every 10 minutes when they are older than 10 minutes. The cleanup only touches `MUSIC_TMP_DIR` (default `/tmp/hmb-nexus-music`) and never deletes the economy database.

## Render

1. Create a PostgreSQL database in the same Render workspace/region.
2. Connect the PostgreSQL database to the `hmb-global` web service, or add its internal `DATABASE_URL` as an environment variable.
3. Redeploy HMB NEXUS.
4. Logs should include:
   `Economy database: PostgreSQL`

Do not remove `DISCORD_TOKEN` or existing YouTube secrets.

## Important

The code keeps a JSON fallback for local development. For Render production persistence, `DATABASE_URL` must be present.
