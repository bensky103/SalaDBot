# SaladBot Architecture Documentation

## Overview
SaladBot is a WhatsApp chatbot that helps customers query a deli/salad menu. It uses a **unified single-LLM architecture** with OpenAI GPT-4o-mini and function calling. All hard-coded pattern matching and router logic has been removed. The LLM naturally handles greetings, orders, category requests, and menu searches in one context-aware call.

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
    ┌──────────────────────────────────────────────────┐
    │  STEP 2: Main LLM Flow (with full context)      │
    │  - Original user_message + full history         │
    │  - LLM resolves context/pronouns naturally      │
    │  - Calls get_menu_items tool                    │
    │  - Queries Supabase (ai_core.py)                │    
    │  - Excludes shown dishes                        │
    │  - Formats response                             │
    └──────────────────────────────────────────────────┘
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
  - `/test-message` (POST) - Development test endpoint
  - **Production**: Uses `ChatService` with unified single-LLM architecture

### **WhatsApp Integration**
- **`whatsapp.py`** - WhatsApp Cloud API client
  - `WhatsAppClient.send_text_message()` - Sends messages to users
  - `parse_webhook_payload()` - Extracts user_id and message from webhook
  - `verify_webhook_signature()` - Security validation (HMAC)

### **Core Logic (Unified Single LLM)**
- **`chat_service.py`** - Production architecture with single LLM call
  - `process_user_message()` - **Main Flow**: Unified conversation handler
    - Builds full context with conversation history
    - Loads instructions.txt for LLM guidance
    - Single GPT-4o-mini call with function calling enabled
    - LLM naturally detects intent and responds appropriately
    - Manages session history via `SessionManager`
    - Tracks shown dishes for variety (no repeats)
  
  **Example Flow:**
  ```python
  # User: "היי, מה קורה?"
  # LLM reads instructions → Detects greeting → Returns business info
  
  # User: "יש לכם מנות בשר?"
  # LLM → Calls get_menu_items(category="בשר") → Returns 5 dishes
  
  # User: "אני רוצה להזמין"
  # LLM reads instructions → Detects order → Returns redirect message
### **Database & AI**
- **`ai_core.py`** - Database queries + OpenAI tool schema
  - `GET_MENU_ITEMS_TOOL` - OpenAI function calling schema (defines parameters)
    - Parameter descriptions guide LLM to use HEBREW values
    - Enum constraints for dietary restrictions
  - `get_menu_items_implementation()` - Queries Supabase PostgreSQL
    - Filters: category, max_price, dietary_restriction, search_term, availability_day
    - Allergen safety: Checks BOTH `allergens_contains` AND `allergens_traces`
    - Excludes previously shown dishes via `exclude_ids`
    - **Retry mechanism**: Fuzzy matching if exact category fails
  - `_retry_query_with_fallbacks()` - Handles typos and alternative spellings
    - Strategy 1: Fuzzy search across name/description/category
    - Strategy 2: Alternative spellings (e.g., 'ספיישל שישי' variants)
  - `_filter_allergen_exclusion()` - CRITICAL safety filter
    - Checks BOTH contains AND traces fields
    - Multiple pattern matching per allergen
  - `format_menu_items_for_ai()` - Formats DB results for LLM consumption
  - `get_category_total_count()` - Counts dishes in category (for future counter feature)
  
  **Example Query:**
  ```python
  get_menu_items_implementation(
      category="בשר",              # Hebrew category
      max_price=10.0,
      dietary_restriction="gluten", # Excludes items with gluten
      exclude_ids=[1, 2, 3]         # Don't repeat these dishes
  )
  # Returns: List of up to 5 dishes (name, price, allergens, availability)
  ``` Excludes previously shown dishes via `exclude_ids`
  - `format_menu_items_for_ai()` - Formats DB results for LLM consumption
  
  **Example Query:**
### **State Management**
- **`session_manager.py`** - User session and conversation history
  - `get_history()` - Retrieves last N messages for context
  - `add_message()` - Stores user/assistant messages
  - `get_shown_dishes()` - Tracks which dish IDs were shown (for variety)
  - `add_shown_dishes()` - Adds new dish IDs to exclusion list
  - `clear_session()` - Resets entire user session
  - **Unimplemented features** (available but not used):
    - `set_category_context()` - Category counter tracking
    - `get_category_context()` - Retrieve counter state
    - `add_category_shown_dishes()` - Category-specific tracking
    - `get_category_shown_count()` - Count dishes in current category
  - Uses in-memory dict (resets on server restart)
  - Auto-cleanup of expired sessions (30 min timeout)
  # Returns: List of 5 dishes (name, price, allergens, availability)
  ```

### **State Management**
### **Utilities**
- **`utils.py`** - Helper functions
  - `get_category_list_message()` - Returns Hebrew category list (static content)
  - `get_business_info_message()` - Returns store hours/info (static content)
  - `get_allergen_safety_message()` - Shared kitchen warning (unused - LLM generates responses)
  - Date/time utilities:
    - `get_current_day_hebrew()` - Current day in Hebrew format
    - `parse_hebrew_day_range()` - Parses "ימים א - ה" format
    - `is_item_available_today()` - Checks availability
  - Validation utilities:
    - `is_valid_whatsapp_id()` - Phone number format validation
    - `format_phone_number()` - Cleans phone numbers
  - Message utilities:
    - `truncate_message()` - WhatsApp 4096 char limit
    - `mask_sensitive_data()` - For logging
  - **NOTE**: All hard-coded pattern matching functions removed (Dec 13, 2025))

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

## Conversation Examples

### **Greeting Detection**
LLM detects greeting and returns business info:
```
User: "היי, מה קורה?"
LLM: Detects greeting → Returns business info message
Response: "שלום! ברוכים הבאים לפיקניק מעדנים... 👋"
```

### **Menu Query**
LLM calls get_menu_items function:
```
User: "תראה לי מנות בשר"
LLM: Calls get_menu_items(category="בשר")
Response: 
  חזה עוף בשומשום - 9₪ ל-100 גרם
  לביבה בשר - 9₪ ל-100 גרם
  פלפל ממולא בשר - 11₪ ל-100 גרם
  ...
```

### **Order Request**
LLM detects order intent and redirects:
```
User: "אני רוצה להזמין"
LLM: Detects order → Returns redirect message
Response: "אשמח לעזור! אני בוט מידע... להזמנה: https://order.picnicmaadanim.co.il"
```

### **Context Awareness**
LLM maintains context naturally:
```
User: "יש לכם מנות טבעוניות?"
LLM: Calls get_menu_items(dietary_restriction="vegan")
Response: [5 vegan dishes]

User: "ואיזה קינוחים?"
LLM: Understands context → Calls get_menu_items(category="קינוחים", dietary_restriction="vegan")
Response: [Vegan desserts only]
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
[LLM] → Calls get_menu_items function
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
---

## Current State (Updated: Dec 13, 2025 - Latest)

✅ **Production-Ready**: Unified single-LLM architecture with function calling
✅ **No Hard-Coded Logic**: All pattern matching removed
✅ **Full Context Preservation**: Original messages + history passed to LLM
✅ **All Tests Passing**: test_agent.py, test_enhanced_agent.py, test_allergen_message.py, test_retry_mechanism.py

### **Latest Migration (Dec 13, 2025):**
1. ✅ Removed `rewrite_user_query()` function (36 lines deleted)
2. ✅ Removed router entirely - unified to single LLM call with function calling
3. ✅ Fixed context loss - original messages now passed directly
4. ✅ Enhanced `instructions.txt` with context awareness guidance
5. ✅ Reduced API calls by 33% (2 calls instead of 3)

### **Previous Migration (Dec 13, 2025 - Earlier):**
1. ✅ Removed `agent.py` entirely (371 lines deleted)
2. ✅ Removed hard-coded detection functions from `utils.py` (164 lines deleted)
3. ✅ Updated `main.py` to use `ChatService` (production webhook)
4. ✅ Updated all test scripts to use async `ChatService`

### **Architecture Benefits:**
- **Perfect context preservation** - No information loss between steps
- **Faster** - One less API call per request
- **Cheaper** - 33% reduction in API costs
- **More natural** - LLM sees conversation as humans do
- **No false positives** - LLM understands context better than regex
- **Handles typos** - "גלטון" works as well as "גלוטן"
- **Context-aware** - Follow-up queries maintain filters naturally
- **Zero maintenance** - No keyword lists to update
- **Extensible** - Easy to add new categories/features

### **System Status:**
- **Retry Mechanism**: ✅ Implemented & tested
- **Allergen Safety**: ✅ Dual-field checking enforced
- **Price Format**: ✅ Always includes units (ל-100 גרם/ליחידה)
- **Dish Variety**: ✅ Tracks and excludes shown dishes
- **Hebrew Support**: ✅ All responses and DB queries in Hebrew
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
3. Monitor LLM intent detection accuracy with real conversations
