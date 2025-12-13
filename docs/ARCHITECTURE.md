# SaladBot Architecture Documentation

## Overview
SaladBot is a WhatsApp chatbot that helps customers query a deli/salad menu. It uses a **3-layer Router Pattern** with OpenAI GPT-4o-mini for intelligent query classification and response generation.

---

## Request Flow (End-to-End)

```
[WhatsApp User] 
    ↓ 
    "היי, איזה מנות יש לכם?"
    ↓
[WhatsApp Cloud API]
    ↓ (webhook POST)
[main.py - FastAPI Server]
    ↓ (parse webhook)
[whatsapp.py - parse_webhook_payload()]
    ↓ (extract user_id, message)
[chat_service.py - ChatService.process_user_message()]
    ↓
┌──────────────────────────────────────┐
│  STEP 1: Router (classify_intent)   │
│  GPT-4o-mini analyzes message        │
│  Returns: CATEGORY | SEARCH | CHAT  │
└──────────────────────────────────────┘
    ↓
    ├─→ [CATEGORY] → get_category_list_message() → Return category list
    │
    ├─→ [CHAT] → Direct LLM response (no database)
    │
    └─→ [SEARCH] → Continue to Step 2
            ↓
    ┌──────────────────────────────────────┐
    │  STEP 2: Rewriter                    │
    │  Converts message to standalone      │
    │  Hebrew query (resolves pronouns)    │
    └──────────────────────────────────────┘
            ↓
            "מה המנות של בשר?"
            ↓
    ┌──────────────────────────────────────┐
    │  STEP 3: Main LLM Flow               │
    │  - Calls get_menu_items tool         │
    │  - Queries Supabase (ai_core.py)     │    
    │  - Excludes shown dishes             │
    │  - Formats response                  │
    └──────────────────────────────────────┘
    ↓
    Bot Response (Hebrew)
    ↓
[whatsapp.py - send_text_message()]
    ↓
[WhatsApp Cloud API]
    ↓
[WhatsApp User receives reply]
```

---

## File-by-File Breakdown

### **Entry Point**
- **`main.py`** - FastAPI server
  - `/webhook` (GET) - Verification endpoint for WhatsApp webhook setup
  - `/webhook` (POST) - Receives incoming WhatsApp messages
  - `/health` - Health check for monitoring
  - Delegates message handling to `agent.py` or `chat_service.py`

### **WhatsApp Integration**
- **`whatsapp.py`** - WhatsApp Cloud API client
  - `WhatsAppClient.send_text_message()` - Sends messages to users
  - `parse_webhook_payload()` - Extracts user_id and message from webhook
  - `verify_webhook_signature()` - Security validation (HMAC)

### **Core Logic (Router Pattern)**
- **`chat_service.py`** - NEW Router-based architecture (3-step pipeline)
  - `classify_intent()` - **Router**: Classifies message as CATEGORY/SEARCH/CHAT
  - `rewrite_user_query()` - **Rewriter**: Converts to standalone Hebrew query
  - `process_user_message()` - **Main Flow**: Orchestrates entire pipeline
  
  **Example Flow:**
  ```python
  # User: "היי, איזה מנות יש לכם?"
  intent = await classify_intent(...)  # Returns: "CATEGORY"
  response = get_category_list_message()  # Returns category list
  
  # User: "תראה לי מנות בשר"
  intent = await classify_intent(...)  # Returns: "SEARCH"
  rewritten = await rewrite_user_query(...)  # "מה המנות של בשר?"
  # Calls get_menu_items(category="בשר") → Returns 5 dishes
  ```

### **Legacy Agent (Deprecated)**
- **`agent.py`** - OLD agent with hard-coded logic
  - `SaladBotAgent.process_message()` - Original flow (before router pattern)
  - Still contains dish tracking and tool execution logic
  - **Status**: Being replaced by `chat_service.py`

### **Database & AI**
- **`ai_core.py`** - Database queries + OpenAI tool schema
  - `GET_MENU_ITEMS_TOOL` - OpenAI function calling schema (defines parameters)
  - `get_menu_items_implementation()` - Queries Supabase PostgreSQL
    - Filters: category, max_price, dietary_restriction, search_term, availability_day
    - Allergen safety: Checks BOTH `allergens_contains` AND `allergens_traces`
    - Excludes previously shown dishes via `exclude_ids`
  - `format_menu_items_for_ai()` - Formats DB results for LLM consumption
  
  **Example Query:**
  ```python
  get_menu_items_implementation(
      category="בשר",              # Hebrew category
      max_price=10.0,
      dietary_restriction="gluten", # Excludes items with gluten
      exclude_ids=[1, 2, 3]         # Don't repeat these dishes
  )
  # Returns: List of 5 dishes (name, price, allergens, availability)
  ```

### **State Management**
- **`session_manager.py`** - User session and conversation history
  - `get_history()` - Retrieves last N messages for context
  - `add_message()` - Stores user/assistant messages
  - `get_shown_dishes()` - Tracks which dish IDs were shown (for variety)
  - `add_shown_dishes()` - Adds new dish IDs to exclusion list
  - Uses in-memory dict (resets on server restart)

### **Utilities**
- **`utils.py`** - Helper functions
  - `get_category_list_message()` - Returns Hebrew category list
  - `get_business_info_message()` - Returns store hours/info
  - `is_greeting_or_generic()` - Detects greetings
  - Date/time utilities for availability checking

### **Configuration & Models**
- **`config.py`** - Environment variables loader
  - Loads `.env` file (API keys, tokens)
- **`models.py`** - Pydantic data models
  - Request/response schemas for type safety

---

## Router Classification Examples

### **CATEGORY Mode**
Triggers when user asks for general overview:
```
User: "היי, איזה מנות יש לכם?"
Router: CATEGORY
Response: [Full category list - סלטים, בשר, עוף, דגים, etc.]
```

### **SEARCH Mode**
Triggers when user asks about specific dishes/categories:
```
User: "תראה לי מנות בשר"
Router: SEARCH
Rewriter: "מה המנות של בשר?"
Tool Call: get_menu_items(category="בשר")
Response: 
  חזה עוף בשומשום - 9₪ ל-100 גרם
  לביבה בשר - 9₪ ל-100 גרם
  פלפל ממולא בשר - 11₪ ל-100 גרם
  ...
```

### **CHAT Mode**
Triggers for greetings, thanks, complaints:
```
User: "תודה רבה!"
Router: CHAT
Response: [Polite acknowledgment, no database query]
```

---

## Key Business Rules (Enforced in Code)

1. **Strict Allergen Safety** (`ai_core.py`)
   - Checks BOTH `allergens_contains` AND `allergens_traces`
   - If EITHER field contains allergen → item excluded

2. **Pricing Format** (`docs/instructions.txt`)
   - All prices must show "ל-100 גרם" or "ליחידה"

3. **Hebrew-Only Database** (`ai_core.py`)
   - Categories: `בשר`, `עוף`, `דגים`, `סלטים`, etc.
   - Allergens: `גלוטן`, `ביצים`, `אגוזים`, etc.

4. **Dish Variety** (`session_manager.py`)
   - Tracks shown dishes per user
   - Excludes them in subsequent queries
   - Prevents repetition

5. **No Ordering** (`docs/instructions.txt`)
   - Bot is informational only
   - Never asks "want to order?"

---

## Data Flow: Database Query

```
User Query: "מנות ללא גלוטן"
    ↓
[Router] → SEARCH
    ↓
[Rewriter] → "מה המנות ללא גלוטן?"
    ↓
[LLM with Tool] → get_menu_items(dietary_restriction="gluten_free")
    ↓
[ai_core.py] 
    query = supabase.table('menu_items').select('*')
    query = query.eq('is_gluten_free', True)
    query = query.limit(5)
    ↓
[Supabase PostgreSQL]
    SELECT * FROM menu_items 
    WHERE is_gluten_free = TRUE 
    LIMIT 5;
    ↓
[format_menu_items_for_ai()]
    Formats: "חומוס - 6₪ ל-100 גרם | ⚠️גלוטן | 📅ימים א - ה"
    ↓
[LLM Final Response]
    Removes internal markers (⚠️, 📅)
    Returns clean Hebrew list
    ↓
[User receives message]
```

---

## Configuration Files

- **`.env`** - Environment variables (API keys)
- **`docs/instructions.txt`** - LLM system prompt (response format rules)
- **`docs/database_schema.md`** - Supabase table structure
- **`docs/project_brief.md`** - Business requirements

---

## Current State

✅ **Active**: `chat_service.py` (Router Pattern)  
⚠️ **Legacy**: `agent.py` (Old hard-coded logic)  
🔄 **In Progress**: Full migration to router pattern

**Next Steps**:
1. Replace all calls to `agent.py` with `chat_service.py`
2. Remove hard-coded logic from `utils.py`
3. Test router accuracy with real conversations
