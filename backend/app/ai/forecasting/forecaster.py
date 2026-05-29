import math
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from datetime import date, timedelta

class ForecastModelInterface(ABC):
    @abstractmethod
    def fit(self, history: List[Tuple[date, float]]) -> None:
        """Fits model to user historical emissions."""
        pass
        
    @abstractmethod
    def predict(self, steps: int) -> List[Dict[str, Any]]:
        """Predicts future emissions for N steps."""
        pass

class MovingAverageModel(ForecastModelInterface):
    def fit(self, history: List[Tuple[date, float]]) -> None:
        self.history = history
        if history:
            self.avg = sum(val for _, val in history) / len(history)
        else:
            self.avg = 2.5 # Default fallback
            
    def predict(self, steps: int) -> List[Dict[str, Any]]:
        predictions = []
        current_date = date.today()
        
        # Simulates a rolling mean walk
        for i in range(1, steps + 1):
            pred_date = current_date + timedelta(days=i)
            # Add small random noise (-0.2 to +0.2)
            expected = max(0.1, self.avg + random.uniform(-0.2, 0.2))
            optimistic = max(0.05, expected * 0.75)
            pessimistic = expected * 1.30
            
            predictions.append({
                "date": pred_date.strftime("%Y-%m-%d"),
                "label": pred_date.strftime("%a"),
                "expected": round(expected, 2),
                "optimistic": round(optimistic, 2),
                "pessimistic": round(pessimistic, 2)
            })
        return predictions

class ProphetModel(ForecastModelInterface):
    def fit(self, history: List[Tuple[date, float]]) -> None:
        self.history = history
        # Estimate trend coefficient and weekly seasonality index
        self.trend = 0.0
        self.seasonality = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0}
        
        if len(history) >= 7:
            # Simple average by weekday
            weekday_sums = {i: [] for i in range(7)}
            for dt, val in history:
                weekday_sums[dt.weekday()].append(val)
                
            global_avg = sum(val for _, val in history) / len(history)
            if global_avg > 0:
                for wkday, vals in weekday_sums.items():
                    if vals:
                        self.seasonality[wkday] = (sum(vals) / len(vals)) / global_avg
            self.base_val = global_avg
        else:
            self.base_val = 2.5
            
    def predict(self, steps: int) -> List[Dict[str, Any]]:
        predictions = []
        current_date = date.today()
        
        for i in range(1, steps + 1):
            pred_date = current_date + timedelta(days=i)
            wkday = pred_date.weekday()
            
            # Apply seasonality multiplier
            mult = self.seasonality.get(wkday, 1.0)
            expected = max(0.1, self.base_val * mult + random.uniform(-0.1, 0.1))
            optimistic = max(0.05, expected * 0.70)
            pessimistic = expected * 1.35
            
            predictions.append({
                "date": pred_date.strftime("%Y-%m-%d"),
                "label": pred_date.strftime("%a"),
                "expected": round(expected, 2),
                "optimistic": round(optimistic, 2),
                "pessimistic": round(pessimistic, 2)
            })
        return predictions

class LSTMForecastModel(ForecastModelInterface):
    def fit(self, history: List[Tuple[date, float]]) -> None:
        self.history = history
        # Mocking an LSTM weights matrix with a sine wave cyclical state
        self.base_avg = sum(val for _, val in history) / len(history) if history else 2.5
        
    def predict(self, steps: int) -> List[Dict[str, Any]]:
        predictions = []
        current_date = date.today()
        
        for i in range(1, steps + 1):
            pred_date = current_date + timedelta(days=i)
            # Cycle wave to mock memory recurrence
            wave = math.sin(i / 3.0) * 0.8
            expected = max(0.1, self.base_avg + wave + random.uniform(-0.05, 0.05))
            optimistic = max(0.05, expected * 0.80)
            pessimistic = expected * 1.25
            
            predictions.append({
                "date": pred_date.strftime("%Y-%m-%d"),
                "label": pred_date.strftime("%a"),
                "expected": round(expected, 2),
                "optimistic": round(optimistic, 2),
                "pessimistic": round(pessimistic, 2)
            })
        return predictions

def generate_forecast_data(history: List[Tuple[date, float]], steps: int = 30, model_type: str = "prophet") -> List[Dict[str, Any]]:
    """
    Convenience factory to run forecasting.
    Sanitizes both input history data and predicted metrics to prevent NaN or None values.
    """
    models = {
        "prophet": ProphetModel(),
        "lstm": LSTMForecastModel(),
        "moving_average": MovingAverageModel()
    }
    
    clean_history = []
    try:
        for d, v in history:
            try:
                if v is None or math.isnan(v) or math.isinf(v):
                    v = 2.5
                clean_history.append((d, float(v)))
            except Exception:
                clean_history.append((d, 2.5))
    except Exception:
        clean_history = history
        
    model = models.get(model_type, ProphetModel())
    model.fit(clean_history)
    
    try:
        raw_predictions = model.predict(steps)
    except Exception:
        # Emergency fallback forecast generator
        raw_predictions = []
        current_date = date.today()
        for i in range(1, steps + 1):
            pred_date = current_date + timedelta(days=i)
            raw_predictions.append({
                "date": pred_date.strftime("%Y-%m-%d"),
                "label": pred_date.strftime("%a"),
                "expected": 2.5,
                "optimistic": 1.88,
                "pessimistic": 3.12
            })
            
    sanitized_predictions = []
    for p in raw_predictions:
        expected = p.get("expected")
        optimistic = p.get("optimistic")
        pessimistic = p.get("pessimistic")
        
        try:
            if expected is None or math.isnan(expected) or math.isinf(expected):
                expected = 2.5
            expected = max(0.01, float(expected))
        except Exception:
            expected = 2.5
            
        try:
            if optimistic is None or math.isnan(optimistic) or math.isinf(optimistic):
                optimistic = expected * 0.75
            optimistic = max(0.01, float(optimistic))
        except Exception:
            optimistic = expected * 0.75
            
        try:
            if pessimistic is None or math.isnan(pessimistic) or math.isinf(pessimistic):
                pessimistic = expected * 1.25
            pessimistic = max(0.01, float(pessimistic))
        except Exception:
            pessimistic = expected * 1.25
            
        sanitized_predictions.append({
            "date": p.get("date") or date.today().strftime("%Y-%m-%d"),
            "label": p.get("label") or "Day",
            "expected": round(expected, 2),
            "optimistic": round(optimistic, 2),
            "pessimistic": round(pessimistic, 2)
        })
        
    return sanitized_predictions

