import time
from typing import List, Dict, Any

def parse_receipt_image(filename: str, file_content_length: int = 0) -> List[Dict[str, Any]]:
    """
    Simulates OCR text extraction and semantic keyword identification from bills or receipts.
    Supported mock cases:
    - If filename contains 'electricity' or 'power': extracts grid electricity consumption.
    - If filename contains 'food' or 'grocery' or 'bill': extracts curd rice, chicken biryani, or vegetables.
    - Default fallback: extracts a general activity.
    """
    # Simulate processing latency
    time.sleep(0.5)
    
    fname = filename.lower()
    extracted = []
    
    if "electricity" in fname or "power" in fname or "bill" in fname and "food" not in fname:
        # Extract power consumption
        extracted.append({
            "text": "Electricity Bill Log: 120 kWh consumed",
            "category": "electricity",
            "item": "grid electricity",
            "quantity": 120.0,
            "unit": "kWh"
        })
    elif "food" in fname or "grocery" in fname or "restaurant" in fname or "cafe" in fname:
        # Extract meal items
        extracted.append({
            "text": "Seeded from receipt: 1 plate chicken biryani",
            "category": "food",
            "item": "chicken biryani",
            "quantity": 1.0,
            "unit": "plate"
        })
        extracted.append({
            "text": "Seeded from receipt: 2 plate curd rice",
            "category": "food",
            "item": "curd rice",
            "quantity": 2.0,
            "unit": "plate"
        })
    else:
        # Generic receipt check fallback
        extracted.append({
            "text": "Seeded from invoice: Travelled 15 km by petrol car",
            "category": "transport",
            "item": "petrol car",
            "quantity": 15.0,
            "unit": "km"
        })
        
    return extracted
