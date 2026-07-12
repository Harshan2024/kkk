# CarbonTracker AI — Carbon Engine Report

**Date:** 2026-07-12  
**Status:** 🤖 COMPLIANT & ACCURATE

---

## 1. Emission Factor Mapping

The Carbon calculation engine maps entities to validated international standard databases (DEFRA, EPA, and IPCC):

| Category | Item Name | Default Emission Factor | Formula |
| :--- | :--- | :--- | :--- |
| **Transport** | `car` | `0.170 kg/km` | `distance * factor` |
| **Food** | `beef` | `27.0 kg/kg` | `weight * factor` |
| **Food** | `poultry` | `6.9 kg/kg` | `weight * factor` |
| **Energy** | `electricity` | `0.475 kg/kWh`| `hours * wattage * factor` |
| **Waste** | `landfill` | `2.100 kg/kg` | `weight * factor` |

---

## 2. Calculation Validation Limits
To prevent data-entry typos from distorting dashboard analytics, the engine restricts inputs to logical boundaries:
-   **Transport Distance limit**: Maximum `5,000 km` per single record entry.
-   **Food quantity limit**: Maximum `50 kg` per meal.
-   **Energy hours limit**: Maximum `24 hours` per day.
-   Any input exceeding these safety thresholds is flagged for warning validation rather than failing, with fallback defaults applied.
