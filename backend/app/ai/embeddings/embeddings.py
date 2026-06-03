import math
from typing import List

# Predefined concept mapping to create pseudo-embeddings (8-dimensions)
# Dimensions: [Food, Transport, Appliance/Power, Shopping, Waste, Water, Leisure, Business]
CONCEPT_KEYWORDS = [
    ["eat", "food", "rice", "curd", "biryani", "dosa", "idli", "beef", "chicken", "milk", "vegetables", "curry", "lunch", "meal"], # Food
    ["drive", "travel", "car", "km", "miles", "bike", "scooter", "flight", "bus", "train", "metro", "commute", "road"],          # Transport
    ["ac", "cooling", "fan", "electricity", "watts", "kwh", "power", "laptop", "tv", "refrigerator", "machine", "geyser"],     # Appliance
    ["buy", "shop", "clothing", "shirt", "shoes", "jeans", "phone", "electronics", "store", "purchase"],                         # Shopping
    ["waste", "organic", "plastic", "paper", "recycling", "trash", "garbage", "throw"],                                         # Waste
    ["water", "shower", "tap", "litres", "gallons", "flow", "bath"],                                                           # Water
    ["watch", "play", "sleep", "walk", "cycle", "read", "game", "movie"],                                                      # Leisure
    ["office", "college", "work", "meeting", "flight", "travelled"]                                                            # Business/Travel context
]

from app.utils.circuit_breaker import breakers

def get_embedding(text: str) -> List[float]:
    """
    Generates a deterministic 8-dimensional semantic concept vector for any text.
    Failsafe and lightweight, wrapped in a circuit breaker.
    """
    try:
        return breakers["embeddings"].call(_get_embedding, text)
    except Exception:
        # Return uniform vector if breaker is open or calculation fails
        return [1.0 / math.sqrt(8.0)] * 8

def _get_embedding(text: str) -> List[float]:
    """Internal implementation of concept vector generation."""
    try:
        text_clean = text.lower().strip()
        vector = [0.0] * 8
        
        for idx, keywords in enumerate(CONCEPT_KEYWORDS):
            score = 0.0
            for kw in keywords:
                if kw in text_clean:
                    # Give higher weight to exact boundary matches
                    if f" {kw} " in f" {text_clean} ":
                        score += 1.0
                    else:
                        score += 0.4
            vector[idx] = score
            
        # Normalize vector to unit length
        magnitude = math.sqrt(sum(x*x for x in vector))
        if magnitude > 0:
            return [x / magnitude for x in vector]
    except Exception:
        pass
        
    return [1.0 / math.sqrt(8.0)] * 8


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Computes cosine similarity between two vectors of identical dimensions.
    """
    if len(vec1) != len(vec2) or not vec1:
        return 0.0
        
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a*a for a in vec1))
    mag2 = math.sqrt(sum(b*b for b in vec2))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
        
    return dot_product / (mag1 * mag2)
