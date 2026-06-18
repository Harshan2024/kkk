import spacy
from spacy.matcher import PhraseMatcher
from typing import Any, List, Dict
from app.nlp.spacy_service import get_spacy_nlp

class EntityMatcher:
    def __init__(self):
        self.nlp = get_spacy_nlp()
        self.matcher = None
        if self.nlp:
            self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            # Patterns mapping normalized label to terms
            self.patterns = {
                "electric_train": ["electric train"],
                "electric_bus": ["electric bus"],
                "electric_scooter": ["electric scooter"],
                "electric_bike": ["electric bike"],
                "petrol_car": ["petrol car"],
                "diesel_car": ["diesel car"],
                "hybrid_car": ["hybrid car"],
                "cng_car": ["cng car"],
                "auto_rickshaw": ["auto rickshaw", "auto"],
                "domestic_flight": ["domestic flight"],
                "international_flight": ["international flight"],
                "air_conditioner": ["air conditioner", "ac", "air conditioning"],
                "washing_machine": ["washing machine"],
                "vegetarian_meal": ["vegetarian meal", "veg meal"],
                "bicycle": ["bike", "bicycle", "cycle"],
                "taxi": ["cab", "taxi", "uber", "ola"],
                "electric_car": ["ev", "electric car"],
                "metro": ["metro", "subway"],
                "local_train": ["local train"],
                "veg_rice": ["veg rice", "veg fried rice"],
                "curd_rice": ["curd rice"],
                "lemon_rice": ["lemon rice"],
                "paneer_rice": ["paneer rice"],
                "dosa": ["dosa", "plain dosa", "paneer dosa", "masala dosa"],
                "idli": ["idli", "idlis", "idly"],
                "pongal": ["pongal"],
                "laptop_charger": ["laptop charger"],
                "chicken_biriyani": ["chicken biriyani", "chicken biryani"],
                "mutton_biriyani": ["mutton biriyani", "mutton biryani"],
                "sambar_rice": ["sambar rice"],
                "plastic_waste": ["plastic waste"],
                "battery_waste": ["battery waste"],
                "e_waste": ["e-waste", "ewaste"]
            }
            for label, terms in self.patterns.items():
                pattern_docs = [self.nlp.make_doc(text) for text in terms]
                self.matcher.add(label, pattern_docs)

    def match(self, doc_or_text: Any) -> List[Dict[str, Any]]:
        """
        Runs the PhraseMatcher against the input text or doc.
        Returns a list of matches sorted by span length descending.
        """
        if not self.nlp or not self.matcher:
            return []
        
        if isinstance(doc_or_text, str):
            doc = self.nlp(doc_or_text)
        else:
            doc = doc_or_text
            
        matches = self.matcher(doc)
        results = []
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            results.append({
                "label": label,
                "text": span.text,
                "start": start,
                "end": end
            })
        
        # Sort by span length descending to prioritize longer phrases (e.g. "electric train" over "train" if any)
        results.sort(key=lambda x: (x["end"] - x["start"]), reverse=True)
        return results

# Shared singleton instance
_matcher = None

def get_entity_matcher() -> EntityMatcher:
    global _matcher
    if _matcher is None:
        _matcher = EntityMatcher()
    return _matcher
