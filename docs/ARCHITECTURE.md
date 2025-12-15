# SaladBot Architecture

> **For AI Agents**: Concise system overview.

## Flow

```
WhatsApp  main.py  chat_service.process_user_message()  OpenAI (function calling)  Response
```

## Core Files

- **app/main.py**: FastAPI webhook endpoint
- **app/chat_service.py**: Main flow (OpenAI + tool execution)
- **app/ai_core.py**: Tool schemas + DB queries (Supabase)
- **app/session_manager.py**: History + shown dishes tracking
- **app/utils.py**: Helper messages
- **app/whatsapp.py**: WhatsApp API client
- **docs/instructions.txt**: LLM behavior rules

## Key Patterns

**Function Calling**:
```python
# LLM calls tools, static tools return directly, get_menu_items needs 2nd LLM call
response = openai.chat.completions.create(messages=..., tools=[...4 tools...])
# Tools: get_business_info, get_order_info, get_category_list, get_menu_items
```

**Dish Exclusion** (prevents repetition):
```python
exclude_ids = session_manager.get_shown_dishes(user_id)
items = get_menu_items_implementation(..., exclude_ids=exclude_ids)
session_manager.add_shown_dishes(user_id, new_dish_ids)
```

**Category Context Tracking** (maintains category across follow-ups):
```python
# Save when explicit, restore when implicit, clear on greeting/category list
session_manager.set_last_category(user_id, category)  # Save
last_category = session_manager.get_last_category(user_id, timeout_minutes=10)  # Restore
session_manager.clear_last_category(user_id)  # Clear
# Example: "איזה קינוחים?" → saves "קינוחים", "יש משהו חלבי?" → uses "קינוחים" filter
```

**Context**: Last 8 messages (4 exchanges)

## Database

- **Table**: menu_items (Supabase PostgreSQL)
- **Language**: ALL data in Hebrew
- **Allergen check**: BOTH llergens_contains AND llergens_traces

## Critical Rules

1. Strict allergen safety (check BOTH fields)
2. Pricing format (must include ל-100 גרם or ליחידה)
3. Hebrew only
4. No invented items (database only)
5. Informational only (no order taking)

