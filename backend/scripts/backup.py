#!/usr/bin/env python3
"""
scripts/backup.py — CarbonTracker AI Database Backup Script
============================================================
Phase 14: Automated database backup with daily/weekly/monthly rotation.

Usage:
    python scripts/backup.py                    # Run a backup now
    python scripts/backup.py --schedule daily   # Label as daily backup
    python scripts/backup.py --retention 30     # Keep 30 days of backups
    python scripts/backup.py --list             # List existing backups
    python scripts/backup.py --cleanup          # Remove expired backups

Backup directory structure:
    backups/
    ├── daily/
    │   └── 2024-07-04_03-00-00_carbontracker.dump
    ├── weekly/
    │   └── 2024-06-30_03-00-00_carbontracker.dump
    └── monthly/
        └── 2024-07-01_03-00-00_carbontracker.dump
"""

import os
import sys
import shutil
import subprocess
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Configuration ─────────────────────────────────────────────────────────────
BACKUP_ROOT = Path(os.getenv("BACKUP_DIR", "./backups"))

RETENTION = {
    "daily":   int(os.getenv("BACKUP_RETENTION_DAILY",   "7")),   # Keep 7 daily backups
    "weekly":  int(os.getenv("BACKUP_RETENTION_WEEKLY",  "4")),   # Keep 4 weekly backups
    "monthly": int(os.getenv("BACKUP_RETENTION_MONTHLY", "12")),  # Keep 12 monthly backups
}

MANIFEST_FILE = BACKUP_ROOT / "backup_manifest.json"


def get_db_url() -> str:
    """Load DATABASE_URL from .env file."""
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set. Cannot run backup.")
    return url


def parse_db_url(url: str) -> dict:
    """Parse postgresql:// URL into component parts."""
    # Strip sslmode params for pg_dump connection string
    base = url.split("?")[0]
    # postgresql://user:pass@host:port/db
    rest = base.replace("postgresql://", "").replace("postgres://", "")
    user_pass, host_db = rest.split("@", 1)
    if ":" in user_pass:
        user, password = user_pass.split(":", 1)
    else:
        user, password = user_pass, ""
    if "/" in host_db:
        host_port, dbname = host_db.rsplit("/", 1)
    else:
        host_port, dbname = host_db, "postgres"
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host, port = host_port, "5432"
    return {"user": user, "password": password, "host": host, "port": port, "dbname": dbname}


def run_backup(schedule: str = "daily") -> Path:
    """Execute pg_dump and save to the appropriate schedule directory."""
    db_url = get_db_url()
    db = parse_db_url(db_url)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = BACKUP_ROOT / schedule
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_file = backup_dir / f"{timestamp}_{db['dbname']}.dump"
    backup_json  = backup_dir / f"{timestamp}_{db['dbname']}.json"

    print(f"[BACKUP] Starting {schedule} backup → {backup_file}")

    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]

    cmd = [
        "pg_dump",
        f"--host={db['host']}",
        f"--port={db['port']}",
        f"--username={db['user']}",
        f"--dbname={db['dbname']}",
        "--format=custom",
        "--compress=9",
        f"--file={backup_file}",
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"[BACKUP] FAILED: {result.stderr}")
        raise RuntimeError(f"pg_dump failed: {result.stderr}")

    # Write metadata JSON
    stat = backup_file.stat()
    metadata = {
        "timestamp": timestamp,
        "schedule": schedule,
        "database": db["dbname"],
        "host": db["host"],
        "file": str(backup_file),
        "size_bytes": stat.st_size,
        "size_human": _human_size(stat.st_size),
        "status": "success",
    }
    backup_json.write_text(json.dumps(metadata, indent=2))

    _update_manifest(metadata)
    print(f"[BACKUP] SUCCESS: {backup_file} ({metadata['size_human']})")
    return backup_file


def cleanup_old_backups():
    """Remove backups exceeding the configured retention periods."""
    print("[CLEANUP] Starting backup rotation...")
    removed = 0

    for schedule, max_count in RETENTION.items():
        backup_dir = BACKUP_ROOT / schedule
        if not backup_dir.exists():
            continue

        # Sort by modification time, newest first
        dumps = sorted(
            backup_dir.glob("*.dump"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for old in dumps[max_count:]:
            print(f"[CLEANUP] Removing expired backup: {old.name}")
            old.unlink(missing_ok=True)
            # Remove associated JSON
            json_file = old.with_suffix(".json")
            json_file.unlink(missing_ok=True)
            removed += 1

    print(f"[CLEANUP] Removed {removed} expired backup(s)")


def list_backups():
    """Print a table of all existing backups."""
    print(f"\n{'Schedule':<10} {'Timestamp':<24} {'Database':<20} {'Size':<12}")
    print("-" * 70)

    total = 0
    for schedule in ["daily", "weekly", "monthly"]:
        backup_dir = BACKUP_ROOT / schedule
        if not backup_dir.exists():
            continue
        for jf in sorted(backup_dir.glob("*.json"), reverse=True):
            try:
                meta = json.loads(jf.read_text())
                print(f"{meta['schedule']:<10} {meta['timestamp']:<24} {meta['database']:<20} {meta['size_human']:<12}")
                total += 1
            except Exception:
                pass

    if total == 0:
        print("  (no backups found)")
    print(f"\nTotal: {total} backup(s) in {BACKUP_ROOT.resolve()}\n")


def _update_manifest(entry: dict):
    """Append entry to the backup manifest JSON log."""
    try:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        entries = []
        if MANIFEST_FILE.exists():
            entries = json.loads(MANIFEST_FILE.read_text())
        entries.append(entry)
        # Keep last 100 entries
        entries = entries[-100:]
        MANIFEST_FILE.write_text(json.dumps(entries, indent=2))
    except Exception as e:
        print(f"[BACKUP] Warning: Could not update manifest: {e}")


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(description="CarbonTracker AI Backup Tool")
    parser.add_argument("--schedule", choices=["daily", "weekly", "monthly"], default="daily")
    parser.add_argument("--retention", type=int, help="Override retention count for this schedule")
    parser.add_argument("--list", action="store_true", help="List existing backups")
    parser.add_argument("--cleanup", action="store_true", help="Remove expired backups only")
    args = parser.parse_args()

    if args.list:
        list_backups()
        return

    if args.cleanup:
        cleanup_old_backups()
        return

    if args.retention:
        RETENTION[args.schedule] = args.retention

    backup_file = run_backup(schedule=args.schedule)
    cleanup_old_backups()
    print(f"[BACKUP] Complete. File: {backup_file}")


if __name__ == "__main__":
    main()
