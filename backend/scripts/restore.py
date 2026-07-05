#!/usr/bin/env python3
"""
scripts/restore.py — CarbonTracker AI Database Restore Script
=============================================================
Phase 14: Restore a database backup created by backup.py

Usage:
    python scripts/restore.py --file backups/daily/2024-07-04_03-00-00_carbontracker.dump
    python scripts/restore.py --latest daily        # Restore most recent daily backup
    python scripts/restore.py --list                # List available backups
    python scripts/restore.py --verify --file <f>   # Verify backup without restoring

WARNING: Restore will DROP and recreate the target database.
         Always verify backup integrity before restoring to production.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKUP_ROOT = Path(os.getenv("BACKUP_DIR", "./backups"))


def get_db_url() -> str:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set.")
    return url


def parse_db_url(url: str) -> dict:
    base = url.split("?")[0]
    rest = base.replace("postgresql://", "").replace("postgres://", "")
    user_pass, host_db = rest.split("@", 1)
    user, password = user_pass.split(":", 1) if ":" in user_pass else (user_pass, "")
    host_port, dbname = host_db.rsplit("/", 1) if "/" in host_db else (host_db, "postgres")
    host, port = host_port.split(":", 1) if ":" in host_port else (host_port, "5432")
    return {"user": user, "password": password, "host": host, "port": port, "dbname": dbname}


def verify_backup(backup_file: Path) -> bool:
    """Run pg_restore --list to check backup integrity without restoring."""
    print(f"[VERIFY] Checking integrity of: {backup_file}")
    result = subprocess.run(
        ["pg_restore", "--list", str(backup_file)],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode == 0:
        table_count = len([l for l in result.stdout.splitlines() if "TABLE DATA" in l])
        print(f"[VERIFY] ✅ Backup is valid. Contains {table_count} table(s).")
        return True
    else:
        print(f"[VERIFY] ❌ Backup is INVALID: {result.stderr}")
        return False


def restore_backup(backup_file: Path, target_db: str = None, confirm: bool = False):
    """Restore a .dump file to the configured database."""
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    db_url = get_db_url()
    db = parse_db_url(db_url)
    target = target_db or db["dbname"]

    print(f"\n{'='*60}")
    print(f"  CarbonTracker AI — Database Restore")
    print(f"{'='*60}")
    print(f"  Source file : {backup_file}")
    print(f"  Target DB   : {target} on {db['host']}:{db['port']}")
    print(f"  Timestamp   : {datetime.utcnow().isoformat()}")
    print(f"{'='*60}\n")

    if not confirm:
        answer = input("⚠️  This will OVERWRITE the target database. Type 'yes' to proceed: ")
        if answer.strip().lower() != "yes":
            print("[RESTORE] Aborted by user.")
            return False

    # Verify backup first
    if not verify_backup(backup_file):
        print("[RESTORE] Restore aborted — backup failed integrity check.")
        return False

    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]
    base_conn = [f"--host={db['host']}", f"--port={db['port']}", f"--username={db['user']}"]

    # Step 1: Terminate active connections to target DB
    print(f"[RESTORE] Terminating active connections to '{target}'...")
    subprocess.run(
        ["psql"] + base_conn + ["--dbname=postgres", "-c",
         f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{target}' AND pid <> pg_backend_pid();"],
        env=env, capture_output=True
    )

    # Step 2: Drop and recreate the database
    print(f"[RESTORE] Dropping database '{target}'...")
    drop = subprocess.run(
        ["dropdb"] + base_conn + ["--if-exists", target],
        env=env, capture_output=True, text=True
    )
    if drop.returncode != 0:
        print(f"[RESTORE] Warning during drop: {drop.stderr}")

    print(f"[RESTORE] Creating database '{target}'...")
    create = subprocess.run(
        ["createdb"] + base_conn + [target],
        env=env, capture_output=True, text=True
    )
    if create.returncode != 0:
        print(f"[RESTORE] ❌ Failed to create database: {create.stderr}")
        return False

    # Step 3: Restore from backup file
    print(f"[RESTORE] Restoring from backup (this may take a few minutes)...")
    restore = subprocess.run(
        ["pg_restore"] + base_conn + [
            f"--dbname={target}",
            "--no-owner",
            "--no-privileges",
            "--verbose",
            str(backup_file)
        ],
        env=env, capture_output=True, text=True, timeout=600
    )

    if restore.returncode == 0:
        print(f"[RESTORE] ✅ Restore completed successfully to '{target}'")
        _write_restore_log(backup_file, target, "success")
        return True
    else:
        # pg_restore may return non-zero for warnings; check stderr
        warnings = [l for l in restore.stderr.splitlines() if "warning" in l.lower()]
        errors = [l for l in restore.stderr.splitlines() if "error" in l.lower()]
        if errors:
            print(f"[RESTORE] ❌ Restore failed with {len(errors)} error(s):\n" + "\n".join(errors[:5]))
            _write_restore_log(backup_file, target, "failed", errors)
            return False
        else:
            print(f"[RESTORE] ✅ Restore completed with {len(warnings)} warning(s) (non-critical).")
            _write_restore_log(backup_file, target, "success_with_warnings", warnings)
            return True


def find_latest_backup(schedule: str = "daily") -> Path:
    """Find the most recent backup for a given schedule."""
    backup_dir = BACKUP_ROOT / schedule
    if not backup_dir.exists():
        raise FileNotFoundError(f"No backups found for schedule '{schedule}' in {backup_dir}")
    dumps = sorted(backup_dir.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dumps:
        raise FileNotFoundError(f"No .dump files found in {backup_dir}")
    return dumps[0]


def list_backups():
    print(f"\n{'Schedule':<10} {'Timestamp':<24} {'Size':<12} {'File'}")
    print("-" * 80)
    found = False
    for schedule in ["daily", "weekly", "monthly"]:
        d = BACKUP_ROOT / schedule
        if not d.exists():
            continue
        for jf in sorted(d.glob("*.json"), reverse=True):
            try:
                meta = json.loads(jf.read_text())
                dump_exists = Path(meta["file"]).exists()
                marker = "✅" if dump_exists else "❌"
                print(f"{meta['schedule']:<10} {meta['timestamp']:<24} {meta['size_human']:<12} {marker} {Path(meta['file']).name}")
                found = True
            except Exception:
                pass
    if not found:
        print("  (no backups found)")
    print()


def _write_restore_log(backup_file: Path, target: str, status: str, details=None):
    log_file = BACKUP_ROOT / "restore_history.json"
    try:
        history = json.loads(log_file.read_text()) if log_file.exists() else []
        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "backup_file": str(backup_file),
            "target_db": target,
            "status": status,
            "details": details or []
        })
        log_file.write_text(json.dumps(history[-50:], indent=2))
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="CarbonTracker AI Restore Tool")
    parser.add_argument("--file", type=str, help="Path to .dump backup file")
    parser.add_argument("--latest", choices=["daily", "weekly", "monthly"],
                        help="Restore the latest backup of the given schedule")
    parser.add_argument("--target-db", type=str, help="Override target database name")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--verify", action="store_true", help="Verify backup integrity only (no restore)")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    if args.list:
        list_backups()
        return

    if args.latest:
        backup_file = find_latest_backup(args.latest)
        print(f"[RESTORE] Found latest {args.latest} backup: {backup_file.name}")
    elif args.file:
        backup_file = Path(args.file)
    else:
        parser.print_help()
        sys.exit(1)

    if args.verify:
        ok = verify_backup(backup_file)
        sys.exit(0 if ok else 1)

    restore_backup(backup_file, target_db=args.target_db, confirm=args.yes)


if __name__ == "__main__":
    main()
