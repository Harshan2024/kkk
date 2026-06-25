#!/usr/bin/env python3
"""
database_backup.py
==================
CarbonTracker AI - Automated Database Backup System.
Dumps all active tables into a portable, structured JSON file.
"""
import sys
import os
import json
import argparse
from datetime import datetime, date

# Add the current directory to the Python path to resolve imports correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database.session import SessionLocal, engine
from app.models import (
    User, Category, EmissionFactor, Activity, SustainabilityScore,
    Achievement, AIInsight, ChatMessage, UserCorrection,
    ActivityEntity, History, Analytics, CoachReport,
    UserSustainabilityProfile, Goal, TrendRecord
)

# Ordered list of models to serialize
MODELS = [
    User, Category, EmissionFactor, Activity, SustainabilityScore,
    Achievement, AIInsight, ChatMessage, UserCorrection,
    ActivityEntity, History, Analytics, CoachReport,
    UserSustainabilityProfile, Goal, TrendRecord
]

def serialize_record(obj):
    """Converts a SQLAlchemy model instance to a dictionary, formatting datetimes to ISO strings."""
    data = {}
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, (datetime, date)):
            data[column.name] = val.isoformat()
        else:
            data[column.name] = val
    return data

def run_backup(output_file: str):
    print(f"[*] Initializing CarbonTracker Database Backup...")
    print(f"[*] Output Target: {output_file}")
    
    db = SessionLocal()
    backup_data = {}
    
    try:
        for model in MODELS:
            table_name = model.__tablename__
            print(f"    - Backing up table: '{table_name}'...")
            records = db.query(model).all()
            backup_data[table_name] = [serialize_record(r) for r in records]
            print(f"      Successfully serialized {len(records)} records.")
            
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
        print(f"[+] Backup completed successfully! Saved in: {output_file}")
        return True
    except Exception as e:
        print(f"[-] CRITICAL ERROR during backup: {e}", file=sys.stderr)
        return False
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CarbonTracker Database Backup System")
    parser.add_argument(
        "--file", 
        type=str, 
        default="carbontracker_backup.json",
        help="Path to save the JSON backup file (default: carbontracker_backup.json)"
    )
    args = parser.parse_args()
    success = run_backup(args.file)
    sys.exit(0 if success else 1)
