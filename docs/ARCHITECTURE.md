# SaladBot Architecture Documentation

## Overview
SaladBot is a WhatsApp chatbot that helps customers query a deli/salad menu. It uses a **simplified 2-step AI-driven Router Pattern** with OpenAI GPT-4o-mini for intelligent query classification and response generation. All hard-coded pattern matching has been removed, and the architecture preserves full conversation context by passing original messages directly to the LLM.

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
  - **Production**: Uses `ChatService` with router pattern

### **WhatsApp Integration**
- **`whatsapp.py`** - WhatsApp Cloud API client
  - `WhatsAppClient.send_text_message()` - Sends messages to users
  - `parse_webhook_payload()` - Extracts user_id and message from webhook
  - `verify_webhook_signature()` - Security validation (HMAC)

### **Core Logic (AI-Driven Router Pattern)**
- **`chat_service.py`** - Production router architecture (3-step pipeline)
  - `classify_intent()` - **Router**: LLM classifies message as CATEGORY/SEARCH/CHAT
    - Uses GPT-4o-mini with temperature=0.0 for consistent classification
    - Bias towards SEARCH (safer to query database than miss a request)
    - No hard-coded patterns - pure AI interpretation
  - `rewrite_user_query()` - **Rewriter**: Converts to standalone Hebrew query
    - Resolves pronouns and context-dependent references
    - Makes query self-contained for better tool calling
  - `process_user_message()` - **Main Flow**: Orchestrates entire pipeline
    - Manages session history via `SessionManager`
    - Tracks shown dishes for variety (no repeats)
    - Handles all 3 intent types (CATEGORY/SEARCH/CHAT)
  
  **Example Flow:**
  ```python
  # User: "היי, איזה מנות יש לכם?"
  intent = await classify_intent(...)  # Returns: "CATEGORY"
  response = get_category_list_message()  # Returns category list
  
  # User: "תראה לי מנות בשר"
  intent = await classify_intent(...)  # Returns: "SEARCH"
  rewritten = await rewrite_user_query(...)  # "מה המנות של בשר?"
  # Calls get_menu_items(category="בשר") → Returns 5 dishes
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
---

## Current State (Updated: Dec 13, 2025 - Latest)

✅ **Production-Ready**: Simplified 2-step AI-driven router pattern
✅ **No Hard-Coded Logic**: All pattern matching removed
✅ **Full Context Preservation**: Original messages + history passed to LLM
✅ **All Tests Passing**: test_agent.py, test_enhanced_agent.py, test_allergen_message.py, test_retry_mechanism.py

### **Latest Migration (Dec 13, 2025):**
1. ✅ Removed `rewrite_user_query()` function (36 lines deleted)
2. ✅ Simplified pipeline from 3-step to 2-step (Router → Main LLM)
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
3. Test router accuracy with real conversations
