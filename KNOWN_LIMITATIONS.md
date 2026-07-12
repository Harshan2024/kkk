# CarbonTracker AI — Known Limitations

The following limitations are present in CarbonTracker AI version 1.0.0 and will be addressed in future minor/major releases:

---

## 1. AI Parsing & NLP Limitations
-   **Contextual Ambiguity**: If a user logs an activity without numerical values or explicit units (e.g. `"I took a trip"` or `"I ate"`), the engine applies default conservative fallbacks (`1.0 unit`).
-   **Limited Multilingual Support**: The parser is trained on English datasets. Entering activity descriptions in other languages might trigger unprocessable warnings or require manual correction.

---

## 2. Scalability Fallbacks
-   **In-Memory Fallback Cache**: The application supports Redis caches. If `REDIS_URL` is omitted, the cache falls back to in-memory TTL maps, which does not share cache keys across scaling container instances.
-   **In-Process Task Queue**: Background tasks (like logging notifications or daily metrics resets) fall back to in-process memory queue loops if Kafka or RabbitMQ URL values are missing.

---

## 3. Deployment Constraints
-   **Offline IoT Sync**: The IoT sensor endpoint is simulated. Live sync requires configuring proprietary device hardware bridges.
-   **Voice Logging Browser support**: Web Speech API dictation is supported in Chrome, Safari, and WebKit-based browsers. Firefox and other platforms fallback to text-only inputs.
