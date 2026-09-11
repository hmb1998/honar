"""
HMB NEXUS persistent economy database.

Uses PostgreSQL when DATABASE_URL is configured (recommended for Render).
Falls back to the local JSON file for local development/offline use.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("honar.database")

DEFAULT_USER = {
    "balance": 100,
    "bank": 0,
    "xp": 0,
    "level": 1,
    "inventory": [],
    "last_daily": None,
}


class EconomyDatabase:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.json_file = (
            Path(__file__).resolve().parent / "data" / "economy_data.json"
        )
        self.json_file.parent.mkdir(parents=True, exist_ok=True)

        if self.database_url:
            try:
                import psycopg
                self._psycopg = psycopg
                self._init_postgres()
                self.backend = "postgres"
                logger.info("Economy database: PostgreSQL")
            except Exception:
                logger.exception(
                    "PostgreSQL initialization failed; using local JSON fallback."
                )
                self.backend = "json"
        else:
            self.backend = "json"
            logger.warning(
                "DATABASE_URL is not configured; economy is using local JSON. "
                "Configure Render PostgreSQL for persistent data."
            )

    def _connect(self):
        return self._psycopg.connect(self.database_url)

    def _init_postgres(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS economy_users (
                        user_id TEXT PRIMARY KEY,
                        balance BIGINT NOT NULL DEFAULT 100,
                        bank BIGINT NOT NULL DEFAULT 0,
                        xp BIGINT NOT NULL DEFAULT 0,
                        level INTEGER NOT NULL DEFAULT 1,
                        inventory JSONB NOT NULL DEFAULT '[]'::jsonb,
                        last_daily TEXT
                    )
                    """
                )
            conn.commit()

    @staticmethod
    def _normalize(user: dict[str, Any]) -> dict[str, Any]:
        result = dict(DEFAULT_USER)
        result.update(user or {})
        if not isinstance(result.get("inventory"), list):
            result["inventory"] = []
        return result

    def load(self) -> dict[str, dict[str, Any]]:
        if self.backend == "postgres":
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT user_id, balance, bank, xp, level, inventory, last_daily
                        FROM economy_users
                        """
                    )
                    rows = cur.fetchall()

            data = {
                str(row[0]): self._normalize(
                    {
                        "balance": row[1],
                        "bank": row[2],
                        "xp": row[3],
                        "level": row[4],
                        "inventory": row[5] or [],
                        "last_daily": row[6],
                    }
                )
                for row in rows
            }

            # One-time migration from an existing local JSON file.
            if not data and self.json_file.is_file():
                try:
                    local = json.loads(
                        self.json_file.read_text(encoding="utf-8")
                    )
                    if isinstance(local, dict) and local:
                        self.save(local)
                        data = {
                            str(k): self._normalize(v)
                            for k, v in local.items()
                        }
                        logger.info(
                            "Migrated %d economy users from JSON to PostgreSQL.",
                            len(data),
                        )
                except Exception:
                    logger.exception("Could not migrate local economy JSON.")

            return data

        if not self.json_file.is_file():
            return {}

        try:
            data = json.loads(self.json_file.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError, TypeError):
            logger.exception("Could not read local economy JSON.")
            return {}

    def save(self, data: dict[str, dict[str, Any]]) -> None:
        if self.backend == "postgres":
            with self._connect() as conn:
                with conn.cursor() as cur:
                    for user_id, raw_user in data.items():
                        user = self._normalize(raw_user)
                        cur.execute(
                            """
                            INSERT INTO economy_users
                                (user_id, balance, bank, xp, level, inventory, last_daily)
                            VALUES
                                (%s, %s, %s, %s, %s, %s::jsonb, %s)
                            ON CONFLICT (user_id) DO UPDATE SET
                                balance = EXCLUDED.balance,
                                bank = EXCLUDED.bank,
                                xp = EXCLUDED.xp,
                                level = EXCLUDED.level,
                                inventory = EXCLUDED.inventory,
                                last_daily = EXCLUDED.last_daily
                            """,
                            (
                                str(user_id),
                                int(user["balance"]),
                                int(user["bank"]),
                                int(user["xp"]),
                                int(user["level"]),
                                json.dumps(user["inventory"], ensure_ascii=False),
                                user.get("last_daily"),
                            ),
                        )
                conn.commit()
            return

        temp_path = self.json_file.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(temp_path, self.json_file)
