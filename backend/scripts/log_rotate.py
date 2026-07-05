#!/usr/bin/env python3
"""
scripts/log_rotate.py — CarbonTracker AI Log Rotation Script
=============================================================
Phase 14: Log file rotation and retention management.

- Compresses log files older than 7 days
- Deletes compressed logs older than 30 days
- Reports disk usage of log directory

Usage:
    python scripts/log_rotate.py                     # Run rotation
    python scripts/log_rotate.py --log-dir ./logs    # Custom log dir
    python scripts/log_rotate.py --dry-run           # Preview only
"""

import os
import sys
import gzip
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))
COMPRESS_AFTER_DAYS = int(os.getenv("LOG_COMPRESS_AFTER_DAYS", "7"))
DELETE_AFTER_DAYS = int(os.getenv("LOG_DELETE_AFTER_DAYS", "30"))


def rotate_logs(log_dir: Path, dry_run: bool = False):
    """Compress old logs and delete very old compressed logs."""
    now = datetime.utcnow()
    compress_cutoff = now - timedelta(days=COMPRESS_AFTER_DAYS)
    delete_cutoff = now - timedelta(days=DELETE_AFTER_DAYS)

    compressed = 0
    deleted = 0
    skipped = 0
    errors = 0

    print(f"[LOG ROTATE] Directory: {log_dir.resolve()}")
    print(f"[LOG ROTATE] Compress logs older than {COMPRESS_AFTER_DAYS} days")
    print(f"[LOG ROTATE] Delete compressed logs older than {DELETE_AFTER_DAYS} days")
    print(f"[LOG ROTATE] Dry run: {dry_run}\n")

    if not log_dir.exists():
        print(f"[LOG ROTATE] Log directory does not exist: {log_dir}")
        return

    for log_file in sorted(log_dir.rglob("*")):
        if not log_file.is_file():
            continue

        try:
            mtime = datetime.utcfromtimestamp(log_file.stat().st_mtime)

            # Delete old .gz files past the delete cutoff
            if log_file.suffix == ".gz" and mtime < delete_cutoff:
                size = log_file.stat().st_size
                print(f"  [DELETE] {log_file.name} (age: {(now - mtime).days}d, size: {_human(size)})")
                if not dry_run:
                    log_file.unlink()
                deleted += 1
                continue

            # Compress uncompressed .log files past the compress cutoff
            if log_file.suffix == ".log" and mtime < compress_cutoff:
                gz_path = log_file.with_suffix(".log.gz")
                orig_size = log_file.stat().st_size
                print(f"  [COMPRESS] {log_file.name} → {gz_path.name} ({_human(orig_size)})")
                if not dry_run:
                    with log_file.open("rb") as f_in:
                        with gzip.open(gz_path, "wb", compresslevel=6) as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    # Verify compressed file was created
                    if gz_path.exists():
                        log_file.unlink()
                        compressed += 1
                    else:
                        print(f"    [ERROR] Compression failed for {log_file.name}")
                        errors += 1
                else:
                    compressed += 1
                continue

            skipped += 1

        except Exception as e:
            print(f"  [ERROR] Processing {log_file.name}: {e}")
            errors += 1

    # Disk usage report
    total_size = sum(f.stat().st_size for f in log_dir.rglob("*") if f.is_file())
    print(f"\n[LOG ROTATE] Summary:")
    print(f"  Compressed: {compressed}")
    print(f"  Deleted:    {deleted}")
    print(f"  Skipped:    {skipped}")
    print(f"  Errors:     {errors}")
    print(f"  Disk usage: {_human(total_size)}")

    if dry_run:
        print("\n[LOG ROTATE] Dry run complete — no files were modified.")
    else:
        print("\n[LOG ROTATE] Rotation complete.")


def _human(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(description="CarbonTracker AI Log Rotation")
    parser.add_argument("--log-dir", default=str(LOG_DIR), help="Log directory path")
    parser.add_argument("--compress-after", type=int, default=COMPRESS_AFTER_DAYS,
                        help="Compress logs older than N days (default: 7)")
    parser.add_argument("--delete-after", type=int, default=DELETE_AFTER_DAYS,
                        help="Delete compressed logs older than N days (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no changes")
    args = parser.parse_args()

    global COMPRESS_AFTER_DAYS, DELETE_AFTER_DAYS
    COMPRESS_AFTER_DAYS = args.compress_after
    DELETE_AFTER_DAYS = args.delete_after

    rotate_logs(Path(args.log_dir), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
