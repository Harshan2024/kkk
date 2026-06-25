#!/usr/bin/env python3
"""
database_restore.py
===================
CarbonTracker AI - Automated Database Restoration System.
Drops tables, recreates schema, and populates data from a backup JSON.
"""
import sys
import os
import json
import argparse
from datetime import datetime, date
from sqlalchemy import DateTime, Date, text

# Add the current directory to the Python path to resolve imports correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database.session import SessionLocal, engine, Base
from app.models import (
    User, Category, EmissionFactor, Activity, SustainabilityScore,
    Achievement, AIInsight, ChatMessage, UserCorrection,
    ActivityEntity, History, Analytics, CoachReport,
    UserSustainabilityProfile, Goal, TrendRecord
)

# Ordered list of models to import (safeguards foreign key dependency ordering)
MODELS = [
    User, Category, EmissionFactor, Activity, SustainabilityScore,
    Achievement, AIInsight, ChatMessage, UserCorrection,
    ActivityEntity, History, Analytics, CoachReport,
    UserSustainabilityProfile, Goal, TrendRecord
]

def run_restore(backup_file: str):
    print(f"[*] Initializing CarbonTracker Database Restoration...")
    print(f"[*] Input Source: {backup_file}")
    
    if not os.path.exists(backup_file):
        print(f"[-] ERROR: Backup file not found: {backup_file}", file=sys.stderr)
        return False
        
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
    except Exception as e:
        print(f"[-] ERROR: Failed to parse backup JSON: {e}", file=sys.stderr)
        return False

    db = SessionLocal()
    
    try:
        print("[*] Rebuilding database schema (dropping and recreating tables)...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("[+] Schema successfully rebuilt.")
        
        for model in MODELS:
            table_name = model.__tablename__
            records_data = backup_data.get(table_name, [])
            print(f"    - Restoring table: '{table_name}' ({len(records_data)} records)...")
            
            for item in records_data:
                row_data = {}
                for col_name, val in item.items():
                    if not hasattr(model, col_name):
                        continue
                    col_type = getattr(model, col_name).type
                    
                    if val is not None:
                        if isinstance(col_type, DateTime):
                            row_data[col_name] = datetime.fromisoformat(val)
                        elif isinstance(col_type, Date):
                            row_data[col_name] = date.fromisoformat(val)
                        else:
                            row_data[col_name] = val
                    else:
                        row_data[col_name] = None
                
                db_record = model(**row_data)
                db.add(db_record)
                
            db.commit()
            print(f"      Successfully populated '{table_name}'.")
            
        # Reset PostgreSQL sequences if using postgresql
        if engine.dialect.name == "postgresql":
            print("[*] Synchronizing PostgreSQL sequence values...")
            with engine.connect() as conn:
                for model in MODELS:
                    table_name = model.__tablename__
                    pk_name = "id"
                    try:
                        pk_name = model.__table__.primary_key.columns.keys()[0]
                    except Exception:
                        pass
                    try:
                        conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table_name}', '{pk_name}'), COALESCE(max({pk_name}), 1)) FROM {table_name}"))
                        conn.commit()
                    except Exception as seq_err:
                        print(f"      Warning: Could not reset sequence for '{table_name}': {seq_err}")
            print("[+] PostgreSQL sequence synchronization completed.")

        print("[+] Database restoration completed successfully!")
        return True
    except Exception as e:
        db.rollback()
        print(f"[-] CRITICAL ERROR during database restoration: {e}", file=sys.stderr)
        return False
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CarbonTracker Database Restoration System")
    parser.add_argument(
        "--file", 
        type=str, 
        default="carbontracker_backup.json",
        help="Path to the JSON backup file (default: carbontracker_backup.json)"
    )
    args = parser.parse_args()
    success = run_restore(args.file)
    sys.exit(0 if success else 1)
