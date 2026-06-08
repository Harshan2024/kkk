import time
import sys
from datetime import datetime, timedelta

sys.path.append("c:/Users/tutyr/Downloads/Harshan/New/backend")
from app.database.session import SessionLocal
from app.models import Activity, SustainabilityScore, User

def measure():
    print("Opening database session...")
    t0 = time.time()
    db = SessionLocal()
    print(f"Session opened in {(time.time() - t0)*1000:.1f}ms")
    
    try:
        # 1. Query user
        t_user = time.time()
        user = db.query(User).filter(User.username == "demo_user").first()
        print(f"User query took {(time.time() - t_user)*1000:.1f}ms")
        
        if not user:
            print("demo_user not found")
            return
            
        user_id = user.id
        
        # 2. Query activities (last 14 days)
        t_act = time.time()
        fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= fourteen_days_ago
        ).all()
        print(f"Activities query took {(time.time() - t_act)*1000:.1f}ms (Count: {len(activities)})")
        
        # 3. Query scores (last 14 days)
        t_scores = time.time()
        scores = db.query(SustainabilityScore).filter(
            SustainabilityScore.user_id == user_id,
            SustainabilityScore.date >= (datetime.utcnow().date() - timedelta(days=14))
        ).all()
        print(f"Scores query took {(time.time() - t_scores)*1000:.1f}ms (Count: {len(scores)})")
        
        # 4. Query all scores for streaks
        t_streaks = time.time()
        all_scores = db.query(SustainabilityScore).filter(
            SustainabilityScore.user_id == user_id
        ).all()
        print(f"All scores query for streaks took {(time.time() - t_streaks)*1000:.1f}ms (Count: {len(all_scores)})")
        
    finally:
        db.close()

if __name__ == "__main__":
    measure()
