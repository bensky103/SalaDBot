# Project: SaladBot POC (WhatsApp)

## Objective
A Hebrew-speaking WhatsApp customer service bot for a salad/deli business.
It provides informational answers about the menu, ingredients, and pricing.

## Tech Stack
- **Framework:** Python (FastAPI)
- **Database:** PostgreSQL (Supabase)
- **AI:** OpenAI GPT-4o-mini (using Tools/Function Calling)
- **Platform:** Railway (Hosting), WhatsApp Cloud API (Interface)

## Critical Business Rules
1. **Pricing:** ALL prices are per 100g. Bot MUST append "ל-100 גרם" to every price quote.
2. **Allergens:** Strict safety. Database has `allergens_contains` and `allergens_traces`. If a user mentions an allergy, check BOTH.
3. **Availability:** Check `availability_days` against the current day of the week.
4. **Language:** Hebrew only.
