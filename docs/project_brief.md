# SaladBot - Project Brief

> **For AI Agents**: Quick project overview.

## What It Is
Hebrew WhatsApp bot for deli menu queries (informational only, no ordering).

## Tech Stack
- Python FastAPI + Supabase + OpenAI GPT-4o-mini + WhatsApp Cloud API
- Deployed on Railway

## Critical Business Rules (NON-NEGOTIABLE)
1. **Strict Allergen**: Check BOTH `allergens_contains` AND `allergens_traces`
2. **Pricing**: Must include "ל-100 גרם" or "ליחידה"
3. **Language**: Hebrew only
4. **Factuality**: Database only (no hallucination)
5. **Scope**: Informational only (no order taking)
