from pydantic import BaseModel, Field
from typing import List, Optional

class ActivityHistoryItem(BaseModel):
    name: str
    category: str
    quantity: float
    unit: str
    factor: float
    carbon: float
    formula: Optional[str] = None
    subtotal: Optional[float] = None

class ActivityHistoryRecord(BaseModel):
    id: str
    timestamp: str
    activities: List[ActivityHistoryItem]
    categories: List[str] = Field(default_factory=list)
    total_carbon: float
    source: str = "manual"

class ActivityHistoryCreate(BaseModel):
    id: Optional[str] = None
    timestamp: Optional[str] = None
    activities: List[ActivityHistoryItem]
    source: Optional[str] = "manual"

class HistoryStatistics(BaseModel):
    total_activities: int
    total_carbon: float
    average_carbon: float
    most_frequent_activity: str
    highest_carbon_activity: str
    lowest_carbon_activity: str
