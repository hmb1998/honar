"""
Temporary-file cleanup for HMB NEXUS.

Only files/directories inside the configured temporary music directory are
removed. Persistent economy/user data is never touched.
"""

from __future__ import annotations

import logging
import os
import shutil
import time
from pathlib import Path

logger = logging.getLogger("honar.cleanup")

CLEANUP_INTERVAL_SECONDS = 10 * 60
MAX_TEMP_AGE_SECONDS = 10 * 60
TEMP_ROOT = Path(
    os.getenv("MUSIC_TMP_DIR", "/tmp/hmb-nexus-music")
)


def cleanup_old_temp_files() -> int:
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    now = time.time()
    removed = 0

    for path in list(TEMP_ROOT.iterdir()):
        try:
            age = now - path.stat().st_mtime
            if age < MAX_TEMP_AGE_SECONDS:
                continue

            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            removed += 1
        except OSError:
            logger.exception("Failed to clean temporary path: %s", path)

    if removed:
        logger.info("Temporary cleanup removed %d old item(s).", removed)
    return removed
