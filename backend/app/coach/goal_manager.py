from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Goal, Activity, SustainabilityScore
from app.services.gamification_service import calculate_streaks

class GoalManager:
    def __init__(self, db: Session):
        self.db = db

    def create_goal(
        self,
        user_id: int,
        goal_type: str,
        target_value: float,
        target_date: Optional[datetime] = None,
        metadata_json: Optional[dict] = None
    ) -> Goal:
        """
        Creates a new sustainability goal for the user.
        goal_types: emission_reduction, activity, streak, sustainability_score
        """
        # Close any active goal of the same type to prevent duplicate tracking
        try:
            self.db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.goal_type == goal_type,
                Goal.status == "active"
            ).update({"status": "failed"})
            self.db.commit()
        except Exception:
            self.db.rollback()

        if target_date is None:
            target_date = datetime.utcnow() + timedelta(days=7)

        goal = Goal(
            user_id=user_id,
            goal_type=goal_type,
            target_value=target_value,
            current_value=0.0,
            status="active",
            progress_percentage=0.0,
            created_at=datetime.utcnow(),
            target_date=target_date,
            metadata_json=metadata_json
        )
        self.db.add(goal)
        try:
            self.db.commit()
            self.db.refresh(goal)
        except Exception:
            self.db.rollback()
        return goal

    def get_user_goals(self, user_id: int, status: Optional[str] = None) -> List[Goal]:
        query = self.db.query(Goal).filter(Goal.user_id == user_id)
        if status:
            query = query.filter(Goal.status == status)
        return query.order_by(Goal.created_at.desc()).all()

    def update_goal_progress(self, user_id: int) -> List[Goal]:
        """
        Queries current database metrics and updates progress percentage for all active user goals.
        """
        active_goals = self.db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.status == "active"
        ).all()
        
        if not active_goals:
            return []

        # 1. Fetch current weekly emissions (past 7 days)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        weekly_emissions = self.db.query(func.sum(Activity.calculated_value)).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= week_ago
        ).scalar() or 0.0
        
        # 2. Fetch current streak
        streaks = calculate_streaks(self.db, user_id)
        current_streak = streaks.get("current_streak", 0)
        
        # 3. Fetch latest sustainability score
        latest_score_rec = self.db.query(SustainabilityScore).filter(
            SustainabilityScore.user_id == user_id
        ).order_by(SustainabilityScore.date.desc()).first()
        current_score = latest_score_rec.score if latest_score_rec else 96.0

        for goal in active_goals:
            # Check deadline first
            if goal.target_date and now > goal.target_date:
                # Goal expired
                # For emission_reduction, we check if they successfully kept emissions under target
                if goal.goal_type == "emission_reduction":
                    if weekly_emissions <= goal.target_value:
                        goal.status = "completed"
                        goal.progress_percentage = 100.0
                        goal.completed_at = now
                    else:
                        goal.status = "failed"
                else:
                    goal.status = "failed"
                continue

            if goal.goal_type == "emission_reduction":
                # Emission reduction: e.g. target is a maximum threshold (e.g. keep emissions under 15kg)
                # If current weekly is less than target, progress is 100%
                # Otherwise, it scales down
                goal.current_value = float(weekly_emissions)
                if weekly_emissions <= goal.target_value:
                    progress = 100.0
                else:
                    excess = weekly_emissions - goal.target_value
                    progress = max(0.0, 100.0 - (excess / goal.target_value) * 100.0)
                goal.progress_percentage = round(progress, 1)
                
            elif goal.goal_type == "activity":
                # Activity: target_value is count of activities logged since goal start
                count = self.db.query(func.count(Activity.id)).filter(
                    Activity.user_id == user_id,
                    Activity.logged_at >= goal.created_at
                ).scalar() or 0
                goal.current_value = float(count)
                progress = min(100.0, (count / goal.target_value) * 100.0)
                goal.progress_percentage = round(progress, 1)
                
            elif goal.goal_type == "streak":
                # Streak: target_value is logging streak
                goal.current_value = float(current_streak)
                progress = min(100.0, (current_streak / goal.target_value) * 100.0)
                goal.progress_percentage = round(progress, 1)
                
            elif goal.goal_type == "sustainability_score":
                # Score: target_value is score
                goal.current_value = float(current_score)
                progress = min(100.0, (current_score / goal.target_value) * 100.0)
                goal.progress_percentage = round(progress, 1)

            # Auto-complete goals if progress reaches 100
            if goal.progress_percentage >= 100.0:
                goal.status = "completed"
                goal.completed_at = now

        try:
            self.db.commit()
            for goal in active_goals:
                self.db.refresh(goal)
        except Exception:
            self.db.rollback()

        return active_goals
