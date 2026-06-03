from typing import Dict, Any, Tuple, Optional
from app.ai.embeddings.embeddings import get_embedding, calculate_cosine_similarity
from app.nlp.parser import KEYWORD_MAPPINGS

# List of typical vague mappings to map to canonical keywords
VAGUE_PHRASES = {
    "rode my scooter": "bike",
    "scooter": "bike",
    "used cooling heavily": "ac",
    "chill": "ac",
    "heating": "water heater",
    "commuted": "petrol car",
    "supper": "vegetables",
    "dine": "chicken",
    "lunch": "rice",
    "watched a movie": "tv",
    "doing laundry": "washing machine",
    "working on mac": "laptop"
}

from app.utils.circuit_breaker import breakers

def find_semantic_match(text: str) -> Optional[Tuple[str, float]]:
    """
    Computes semantic similarity between user text and known keywords/phrases.
    Wrapped in semantic_search circuit breaker.
    """
    try:
        return breakers["semantic_search"].call(_find_semantic_match, text)
    except Exception:
        # Fallback to basic case-insensitive substring checks if breaker is open or fails
        text_clean = text.lower().strip()
        for kw in KEYWORD_MAPPINGS.keys():
            if kw in text_clean:
                return kw, 0.80
        return None

def _find_semantic_match(text: str) -> Optional[Tuple[str, float]]:
    """Internal implementation of semantic match search."""
    text_clean = text.lower().strip()
    
    # 1. Direct dictionary check first for typical vague sentences
    for phrase, kw in VAGUE_PHRASES.items():
        if phrase in text_clean:
            return kw, 0.90
            
    try:
        # 2. Vector embedding similarity search
        text_embed = get_embedding(text_clean)
        best_match = None
        best_similarity = 0.0
        
        # Loop over keyword mappings and compute similarity
        for kw in KEYWORD_MAPPINGS.keys():
            kw_embed = get_embedding(kw)
            sim = calculate_cosine_similarity(text_embed, kw_embed)
            
            if sim > best_similarity:
                best_similarity = sim
                best_match = kw
                
        if best_similarity >= 0.70:
            return best_match, best_similarity
    except Exception:
        # Fallback to basic case-insensitive substring checks if embeddings fail
        for kw in KEYWORD_MAPPINGS.keys():
            if kw in text_clean:
                return kw, 0.80
        
    return None


def get_semantic_confidence(text: str, matched_kw: Optional[str], similarity: float) -> Tuple[float, float]:
    """
    Returns (confidence_score, ambiguity_score) for NLP validation.
    """
    if not matched_kw:
        return 0.30, 0.90
        
    # High similarity = high confidence, low ambiguity
    confidence = similarity
    
    # If the match was direct exact word match
    if matched_kw in text.lower():
        confidence = max(confidence, 0.95)
        
    ambiguity = round(1.0 - confidence, 2)
    return round(confidence, 2), ambiguity
