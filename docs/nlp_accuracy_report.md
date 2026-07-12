# CarbonTracker AI — NLP Accuracy Report

**Date:** 2026-07-12  
**Status:** 🤖 VERIFIED & ACCURATE

---

## 1. Intent Detection & Entity Mapping

The natural-language parser parses sustainability inputs using spaCy/Regex rule matching.

| Category | Input Sentence Example | Extracted Item | Quantity | Unit | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Transport** | "I drove 18 km" | `car` | `18.0` | `km` | ✅ Pass |
| **Food** | "I ate chicken biryani" | `chicken biryani` | `1.0` | `meal` | ✅ Pass |
| **Energy** | "Used AC for 4 hours" | `air conditioner` | `4.0` | `hours` | ✅ Pass |
| **Shopping** | "bought cotton t-shirt" | `cotton t-shirt` | `1.0` | `item` | ✅ Pass |
| **Waste** | "composted 1 kg organic" | `organic waste` | `1.0` | `kg` | ✅ Pass |

---

## 2. Multi-Entity Sentence Parsing
The NLP parser handles compound sentences with multiple operations cleanly:
-   **Example**: `"drove 8 km in car and used AC for 2 hours"`
-   **Split Logic**: The tokenizer splits the sentence based on transition words (e.g. `and`, `,`, `then`), creating distinct sub-components:
    1.  `"drove 8 km in car"` -> `quantity = 8.0`, `unit = km`, `item = car`
    2.  `"used AC for 2 hours"` -> `quantity = 2.0`, `unit = hours`, `item = AC`
-   Both are calculated, registered, and saved in a single transactional request.
