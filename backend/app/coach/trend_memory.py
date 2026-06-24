from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Activity, TrendRecord

class TrendMemoryEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_period_emissions(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        val = self.db.query(func.sum(Activity.calculated_value)).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= start_date,
            Activity.logged_at < end_date
        ).scalar()
        return float(val or 0.0)

    def calculate_category_emissions(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        query_res = self.db.query(
            Activity.category,
            func.sum(Activity.calculated_value)
        ).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= start_date,
            Activity.logged_at < end_date
        ).group_by(Activity.category).all()
        
        res = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
        for cat, val in query_res:
            c = cat.lower() if cat else "energy"
            if c in ["electricity", "appliances", "energy"]:
                mapped_cat = "energy"
            elif c in ["food", "transport", "waste"]:
                mapped_cat = c
            else:
                mapped_cat = "energy"
            res[mapped_cat] += float(val or 0.0)
        return res

    def track_trends(self, user_id: int) -> List[TrendRecord]:
        """
        Computes 30-day, 60-day, and 90-day trends, identifies best improvement
        and worst emission periods, determines category improvements, and stores TrendRecords.
        """
        now = datetime.utcnow()
        
        # Calculate trends
        periods = [30, 60, 90]
        records_saved = []
        
        # 1. Weekly bins for the last 90 days to find best/worst periods
        weekly_bins = []
        for i in range(12):
            w_end = now - timedelta(days=i*7)
            w_start = now - timedelta(days=(i+1)*7)
            val = self.calculate_period_emissions(user_id, w_start, w_end)
            weekly_bins.append((w_start, w_end, val))
            
        # Find best improvement (largest drop between consecutive weeks)
        best_imp_str = "None detected"
        max_drop = -1.0
        for i in range(len(weekly_bins) - 1):
            curr_week_val = weekly_bins[i][2]
            prev_week_val = weekly_bins[i+1][2]
            drop = prev_week_val - curr_week_val
            if drop > max_drop:
                max_drop = drop
                best_imp_str = f"Week {i+1} (-{drop:.1f} kgCO2e)"
                
        # Find worst emission period (week with highest emissions)
        worst_val = -1.0
        worst_period_str = "None detected"
        for i, (w_start, w_end, val) in enumerate(weekly_bins):
            if val > worst_val:
                worst_val = val
                worst_period_str = f"Week {i+1} ({val:.1f} kgCO2e)"

        # 2. Most improved and most problematic category in the last 30 days
        cat_curr_30d = self.calculate_category_emissions(user_id, now - timedelta(days=30), now)
        cat_prior_30d = self.calculate_category_emissions(user_id, now - timedelta(days=60), now - timedelta(days=30))
        
        most_improved_cat = "None"
        max_cat_drop = -1.0
        for cat in ["food", "transport", "energy", "waste"]:
            drop = cat_prior_30d.get(cat, 0.0) - cat_curr_30d.get(cat, 0.0)
            if drop > max_cat_drop:
                max_cat_drop = drop
                most_improved_cat = cat
                
        most_prob_cat = max(cat_curr_30d, key=cat_curr_30d.get) if any(cat_curr_30d.values()) else "energy"

        # 3. Consistency Evolution
        # Check active logging days in current 30 days vs prior 30 days
        days_logged_curr = self.db.query(func.count(func.distinct(func.date(Activity.logged_at)))).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= now - timedelta(days=30)
        ).scalar() or 0
        
        days_logged_prior = self.db.query(func.count(func.distinct(func.date(Activity.logged_at)))).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= now - timedelta(days=60),
            Activity.logged_at < now - timedelta(days=30)
        ).scalar() or 0
        
        consistency_str = f"Consistent: logged {days_logged_curr} days recently vs {days_logged_prior} days previously."

        # Delete existing trend records for the user to maintain a clean history of fresh computed runs
        try:
            self.db.query(TrendRecord).filter(TrendRecord.user_id == user_id).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()

        for p_days in periods:
            curr_val = self.calculate_period_emissions(user_id, now - timedelta(days=p_days), now)
            prior_val = self.calculate_period_emissions(user_id, now - timedelta(days=p_days*2), now - timedelta(days=p_days))
            
            trend_pct = 0.0
            if prior_val > 0:
                trend_pct = round(((curr_val - prior_val) / prior_val) * 100.0, 2)
                
            tr = TrendRecord(
                user_id=user_id,
                period_days=p_days,
                trend_pct=trend_pct,
                best_improvement_period=best_imp_str,
                worst_emission_period=worst_period_str,
                most_improved_category=most_improved_cat,
                most_problematic_category=most_prob_cat,
                consistency_evolution=consistency_str
            )
            self.db.add(tr)
            records_saved.append(tr)
            
        try:
            self.db.commit()
            for r in records_saved:
                self.db.refresh(r)
        except Exception as e:
            self.db.rollback()
            
        return records_saved
