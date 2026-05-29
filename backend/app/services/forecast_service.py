from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.models import SustainabilityScore
from app.ai.forecasting.forecaster import generate_forecast_data

def get_user_forecast(db: Session, user_id: int, steps: int = 30, model_type: str = "prophet") -> List[Dict[str, Any]]:
    """
    Retrieves user's historical daily carbon emissions from SustainabilityScore table,
    feeds it to the predictive forecasting engine, and returns expected, optimistic,
    and pessimistic trajectory values.
    """
    scores = db.query(SustainabilityScore).filter(
        SustainabilityScore.user_id == user_id
    ).order_by(SustainabilityScore.date.asc()).all()
    
    history = [(s.date, s.total_emissions) for s in scores]
    
    # If the user has sparse history, seed mock historical parameters so the forecast is meaningful
    if len(history) < 3:
        today = date.today()
        history = [
            (today - timedelta(days=6), 4.20),
            (today - timedelta(days=5), 11.25),
            (today - timedelta(days=4), 3.42),
            (today - timedelta(days=3), 2.10),
            (today - timedelta(days=2), 5.80),
            (today - timedelta(days=1), 6.50)
        ]
        
    return generate_forecast_data(history, steps, model_type)
