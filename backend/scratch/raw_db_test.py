import time
import psycopg2
from app.config.config import settings

t0 = time.time()
print("Connecting raw psycopg2...")
try:
    conn = psycopg2.connect(settings.DATABASE_URL)
    t1 = time.time()
    print(f"Connected in {t1 - t0:.2f} seconds.")
    
    cur = conn.cursor()
    t2 = time.time()
    cur.execute("SELECT 1")
    cur.fetchone()
    t3 = time.time()
    print(f"Executed SELECT 1 in {t3 - t2:.2f} seconds.")
    
    conn.close()
except Exception as e:
    print(f"Failed! {e}")
