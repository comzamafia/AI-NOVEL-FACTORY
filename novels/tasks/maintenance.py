"""
Celery tasks for system maintenance.

Tasks:
  backup_database         — daily pg_dump → compressed .sql.gz file
  cleanup_old_backups     — weekly: delete backups older than BACKUP_RETAIN_DAYS
  health_check            — heartbeat task for monitoring (Flower / UptimeRobot)
"""

import gzip
import logging
import os
import shutil
import subprocess
from datetime import timedelta
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/app/backups"))
BACKUP_RETAIN_DAYS = int(os.getenv("BACKUP_RETAIN_DAYS", "30"))


def _get_db_config() -> dict:
    """Extract DB connection details from DATABASE_URL or settings."""
    import urllib.parse as urlparse

    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        parsed = urlparse.urlparse(db_url)
        return {
            "host": parsed.hostname or "localhost",
            "port": str(parsed.port or 5432),
            "user": parsed.username or "postgres",
            "password": parsed.password or "",
            "dbname": parsed.path.lstrip("/"),
        }

    # Fall back to DATABASES setting
    db = settings.DATABASES.get("default", {})
    return {
        "host": db.get("HOST", "localhost"),
        "port": str(db.get("PORT", 5432)),
        "user": db.get("USER", "postgres"),
        "password": db.get("PASSWORD", ""),
        "dbname": db.get("NAME", "ai_novel_factory"),
    }


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=2, queue="default")
def backup_database(self):
    """
    Create a compressed PostgreSQL dump.

    Output: BACKUP_DIR/novel_factory_YYYYMMDD_HHMMSS.sql.gz
    On failure: retries once after 5 minutes, then logs error.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    dump_file = BACKUP_DIR / f"novel_factory_{timestamp}.sql"
    gz_file = BACKUP_DIR / f"novel_factory_{timestamp}.sql.gz"

    logger.info(f"[Backup] Starting database backup → {gz_file}")

    try:
        cfg = _get_db_config()

        env = os.environ.copy()
        env["PGPASSWORD"] = cfg["password"]

        result = subprocess.run(
            [
                "pg_dump",
                "--host", cfg["host"],
                "--port", cfg["port"],
                "--username", cfg["user"],
                "--no-password",
                "--format", "plain",
                "--file", str(dump_file),
                cfg["dbname"],
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes max
        )

        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr.strip()}")

        # Compress
        with open(dump_file, "rb") as f_in, gzip.open(gz_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

        dump_file.unlink(missing_ok=True)  # remove uncompressed

        size_mb = gz_file.stat().st_size / 1_000_000
        logger.info(f"[Backup] Done — {gz_file.name} ({size_mb:.2f} MB)")

        _notify_backup_success(str(gz_file), size_mb)

        return {
            "status": "success",
            "file": str(gz_file),
            "size_mb": round(size_mb, 2),
            "timestamp": timestamp,
        }

    except Exception as exc:
        logger.error(f"[Backup] Failed: {exc}")
        dump_file.unlink(missing_ok=True)
        gz_file.unlink(missing_ok=True)
        raise self.retry(exc=exc, countdown=300)  # retry after 5 min


@shared_task(queue="default")
def cleanup_old_backups():
    """
    Delete .sql.gz backup files older than BACKUP_RETAIN_DAYS days.
    Runs weekly (configured in CELERY_BEAT_SCHEDULE).
    """
    if not BACKUP_DIR.exists():
        logger.info("[Backup Cleanup] Backup directory does not exist, skipping.")
        return {"deleted": 0}

    cutoff = timezone.now() - timedelta(days=BACKUP_RETAIN_DAYS)
    deleted = 0

    for f in BACKUP_DIR.glob("novel_factory_*.sql.gz"):
        mtime = timezone.datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            f.unlink()
            logger.info(f"[Backup Cleanup] Deleted old backup: {f.name}")
            deleted += 1

    logger.info(f"[Backup Cleanup] Cleaned up {deleted} old backups (>{BACKUP_RETAIN_DAYS} days).")
    return {"deleted": deleted, "cutoff_days": BACKUP_RETAIN_DAYS}


@shared_task(queue="default")
def health_check():
    """
    Heartbeat task — confirms Celery workers are alive.
    Can be monitored via Flower or external uptime services.
    """
    logger.debug("[HealthCheck] Celery worker heartbeat OK")
    return {"status": "ok", "timestamp": timezone.now().isoformat()}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _notify_backup_success(filepath: str, size_mb: float):
    """Log backup success. Extend this to send email/Slack/Sentry alert."""
    logger.info(
        f"[Backup] ✓ Backup successful: {filepath} ({size_mb:.2f} MB) "
        f"at {timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')}"
    )
