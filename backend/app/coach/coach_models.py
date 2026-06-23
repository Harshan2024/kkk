from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class HabitPattern(BaseModel):
    pattern: str
    confidence: float
    category: str

class EnergyHabit(BaseModel):
    finding: str
    ac_hours: float
    ac_percentage: float

class FoodHabit(BaseModel):
    finding: str
    food_profile: str
    veg_ratio: float
    animal_ratio: float

class TransportHabit(BaseModel):
    finding: str
    transport_profile: str
    public_transport_ratio: float

class WasteHabit(BaseModel):
    finding: str
    waste_profile: str
    recycling_frequency: int

class CoachInsight(BaseModel):
    top_source: str
    contribution: float
    lowest_source: str
    best_habit: str
    worst_habit: str
    improvement_opportunity: str

class ScoreExplanation(BaseModel):
    score: int
    grade: str
    reason: List[str]

class WeeklyReport(BaseModel):
    weekly_carbon: float
    top_source: str
    potential_reduction: float
    summary: str

class MonthlyReport(BaseModel):
    monthly_carbon: float
    category_ranking: List[Dict[str, Any]]
    behavior_changes: List[str]
    achievements: List[str]
    recommendations: List[str]

class DayPlan(BaseModel):
    day: int
    task: str

class ActionPlan(BaseModel):
    plan: List[DayPlan]

class HabitAnalysis(BaseModel):
    patterns: List[HabitPattern]
    energy: EnergyHabit
    food: FoodHabit
    transport: TransportHabit
    waste: WasteHabit
