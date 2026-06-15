import time
from sqlalchemy import create_engine, text

def check_url(url):
    print(f"Testing URL: {url}")
    t0 = time.time()
    try:
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=15,
            max_overflow=25,
            pool_recycle=300,
            pool_timeout=15,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"  Success? (should not happen)")
    except Exception as e:
        print(f"  Failed in {time.time() - t0:.2f} seconds. Error: {type(e).__name__}")

check_url("postgresql://postgres:wrongpassword@localhost:5439/nonexistent_db")
check_url("postgresql://postgres:wrongpassword@localhost:5439/nonexistent_db?connect_timeout=1")
check_url("postgresql://postgres:wrongpassword@127.0.0.1:5439/nonexistent_db")
check_url("postgresql://postgres:wrongpassword@127.0.0.1:5439/nonexistent_db?connect_timeout=1")

