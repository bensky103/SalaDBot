# SaladBot - Recent Changes & Key Information

> **For AI Agents**: Concise summary of current state and recent fixes only.  
> **Coding Focus**: Read `docs/` for full specs. This file = recent changes only.

---

## CURRENT ARCHITECTURE

**Single Unified LLM with Function Calling**
```
User  ChatService.process_user_message() 
     OpenAI GPT-4o-mini (function calling)
     Tools: get_business_info | get_order_info | get_category_list | get_menu_items
     Response
```

**Key Components**:
- `chat_service.py`: Main flow, manages tools & history
- `ai_core.py`: Tool schemas + `get_menu_items_implementation()`
- `session_manager.py`: Tracks conversation history + shown dishes (prevents repetition)
- `docs/instructions.txt`: LLM behavior rules

**Context Window**: Last 8 messages (4 user + 4 assistant exchanges)

---

## CRITICAL BUSINESS RULES (Immutable)

1. **Strict Allergen**: Check BOTH `allergens_contains` AND `allergens_traces`
2. **Pricing**: Must include "ל-100 גרם" or "ליחידה"
3. **Factuality**: No invented items (database only)
4. **Language**: Hebrew only
5. **Database**: ALL values in Hebrew (categories, allergens, availability)

---

## RECENT FIXES

### Fix #1: Cross-Category Ingredient Query Bug (2025-12-15)
**Problem**: User browsing cookies asks "מה הרכיבים של מרק ירקות?" → Bot returns "כל המנות בקטגוריה זו כבר הוצגו" (can't find soup)

**Root Cause**: Backend code (`chat_service.py` L191-195) automatically applied saved category context even when LLM correctly sent ONLY `search_term` (no category). This filtered queries to wrong category.

**Solution**: 
- `app/chat_service.py` (L194-199): Skip category context when `search_term` is present (specific dish search)
- `docs/instructions.txt`: Added explicit rules for LLM to not include category in specific dish queries

**Result**: ✅ Ingredient queries work across all categories regardless of browsing context. ✅ Backend no longer restricts search_term queries by category.

---

### Fix #2: Multiple Detail Queries - Temperature Fix + Enhanced Instructions (2025-12-15)
**Problem**: 
1. When user asks "מה הרכיבים שלהם?" for 5 dishes, LLM mixes/jumbles ingredients
2. When user asks "מה האלרגנים?" after showing dishes, bot repeats previous response or returns wrong data

**Root Cause**: 
1. LLM makes 5 parallel tool calls, receives 5 separate responses
2. With `temperature=0.7`, LLM "gets creative" when synthesizing, mixing data between dishes

**Solution**: 
- `app/config.py` (L103): Changed `OPENAI_TEMPERATURE: 0.7 → 0.0` for deterministic responses
- `docs/instructions.txt`: Enhanced with explicit multi-dish formatting instructions:
  - Added step-by-step verification process for mapping tool responses to dishes
  - Explicit "DO NOT mix data between dishes" rules
  - Detailed formatting examples for both ingredients and allergens
  - Clear separation between "מכילה" and "עקבות" for allergen queries

**Previous Approach (Removed 2025-12-15)**:
- Pre-formatting with hard-coded keyword detection (`_is_multiple_ingredient_query`, `_format_multiple_ingredients_response`)
- Limitation: Only detected specific Hebrew keywords, couldn't handle alternative phrasings

**Result**: ✅ Ingredients/allergens never mixed with temp=0.0. ✅ More flexible - handles various phrasings. ✅ All responses more consistent. ✅ LLM-based synthesis with clear instructions.

---

### Fix #3: Category Exhaustion Retry Bug (2025-12-15)
**Problem**: When user asks "מה עוד?" after all עוגיות shown, bot returns קינוחים dishes instead of "all shown" message.

**Root Cause**: Retry mechanism in `get_menu_items_implementation()` triggered even when items list empty due to exclusion (all dishes already shown). Fuzzy search then matched "עוגיות" in other categories' descriptions, returning wrong dishes.

**Solution**: `app/ai_core.py` (L217): Added `and not exclude_ids` condition to retry trigger - only retry for genuinely empty categories, not when all dishes excluded.

**Result**: ✅ Bot correctly responds "זה כל המנות בקטגוריה זו" when category exhausted. ✅ No cross-category contamination.

---

### Fix #4: Prompt Caching Optimization + Extended Context Window (2025-12-15)
**Problem**:
1. System instructions (~4,050 tokens) sent twice per exchange = major token waste (72% of input)
2. Context window limited to 8 exchanges - bot loses context in longer conversations
3. Monthly cost estimate: $350-560 USD due to repeated prompt overhead

**Root Cause**:
1. System message structure had dynamic content (day, category) BEFORE static instructions
2. This breaks OpenAI's auto-caching (needs static prefix for 5-10 min cache at 50% discount)
3. Context window too small for extended conversations (16 messages = 8 exchanges)

**Solution**:
- `app/chat_service.py` (L83-90): Reordered system message - static instructions FIRST, dynamic context LAST
- `app/config.py` (L63): Increased context window: 16→40 messages (8→20 exchanges)
- `app/config.py` (L57): Increased history storage: 20→50 messages (buffer for 20 exchanges)

**Result**: ✅ Prompt caching enabled (50% discount on ~4,050 cached tokens per exchange). ✅ Context maintained for 20 full exchanges. ✅ Estimated cost reduction: ~40-50%.

---

### Fix #5: Category Distinction Bug + Context Loss Fix (2025-12-15)
**Problem**:
1. Bot confused cookies (עוגיות) with desserts (קינוחים)
2. Bot lost category context after 2-3 exchanges, reverting to wrong categories

**Root Cause**:
1. LLM lacked explicit category distinction rules
2. Tool schema didn't list עוגיות as a category (only showed קינוחים)
3. Context window too small (8 messages = 4 exchanges), causing context loss
4. LLM not instructed to respect explicitly mentioned categories in follow-ups
5. `.dockerignore` excluded `docs/` folder → `instructions.txt` not deployed

**Solution**:
- `docs/instructions.txt` (L67-92): Added "CATEGORY DISTINCTIONS" section
- `docs/instructions.txt` (L42-45): Added rule for respecting explicitly mentioned categories ("יש עוד עוגיות?" → must use עוגיות)
- `app/utils.py` (L215-218): Enhanced category list to group sweet categories
- `app/ai_core.py` (L90): Updated tool schema to list all categories + warning
- `.dockerignore` (L30-38): Fixed to include `instructions.txt`

**Result**: ✅ Bot distinguishes dessert categories. ✅ Respects explicit category mentions.

---

### Fix #6: Context-Aware Dish Tracking (2025-12-14)
**Problem**: Bot tracked ALL queries as "shown dishes", even ingredient/detail queries. This caused:
- User asks "מה הרכיבים של קציצות עוף?" → Dish added to shown list
- User asks again "מה הרכיבים?" → Bot refuses, says "all dishes already shown"

**Root Cause**: System added dishes to exclusion list regardless of query intent (browsing vs. details)

**Solution**: Added `track_shown` parameter to `get_menu_items` tool:
- `ai_core.py`: Added `track_shown` boolean parameter to tool schema with clear usage instructions
- `chat_service.py` (L162-197): Conditionally track shown dishes based on `track_shown` value
- `docs/instructions.txt` (L31-36): LLM guidance on when to set `track_shown=true` vs `track_shown=false`
- `scripts/test_track_shown.py`: Comprehensive test suite (5 test cases)

**Result**: ✅ Ingredient/detail queries can be repeated without "already shown" errors. Browsing still prevents repetition.

---

### Fix #7: Dish Repetition (2025-12-13)
**Problem**: Bot repeated same dishes when user asked "show me more"

**Root Cause**: When all dishes filtered by `exclude_ids`, system returned empty list but didn't signal "all shown"

**Solution**:
- `chat_service.py` (L123-144): Detect if returned dishes are NEW
- `ai_core.py` `format_menu_items_for_ai()`: Added `all_shown` parameter
- Returns `"[ALL_DISHES_SHOWN] כל המנות בקטגוריה זו כבר הוצגו."` when exhausted

**Result**: LLM responds "זה כל המנות בקטגוריה זו" instead of repeating

---

### Fix #8: Context Over-Application (2025-12-13)
**Problem**: LLM stuck maintaining filters (e.g., Friday filter persisted forever)

**Solution**: Deleted instruction from `docs/instructions.txt`:
> ~~"When in doubt about context, it's better to maintain the previous filter than to ignore it."~~

**Result**: LLM naturally resets context when user changes topic

---

### Fix #9: Category Context Preservation (2025-12-13)
**Problem**: Bot loses category context in follow-up queries. Example:
- User: "איזה קינוחים יש?" → Bot shows desserts
- User: "יש משהו חלבי?" → Bot searches ALL dairy items instead of dairy desserts

**Root Cause**: Stateless LLM with limited history cannot reliably maintain category context across messages

**Solution**: Session-based category tracking:
- `session_manager.py`: Added `set_last_category()`, `get_last_category()`, `clear_last_category()` with 10-minute timeout
- `chat_service.py`: System prompt includes category hint `[Context: User is currently browsing category 'X']`
- `chat_service.py`: Menu handler saves category when explicit, restores when implicit, clears on greeting/category list
- `docs/instructions.txt`: Added CATEGORY CONTEXT TRACKING rules with explicit examples
- `scripts/test_context_preservation.py`: 8 comprehensive tests validating all scenarios

**Result**: ✅ Follow-up queries maintain category filter automatically (e.g., "יש משהו חלבי?" after "איזה קינוחים?" now searches dairy DESSERTS)

---

## KEY FILES

- **`app/chat_service.py`**: Main conversation flow
- **`app/ai_core.py`**: Database queries + tool schemas
- **`app/session_manager.py`**: History + dish tracking
- **`app/utils.py`**: Helper functions (business info, categories, etc.)
- **`docs/instructions.txt`**: LLM behavior instructions (165 lines)
- **`docs/ARCHITECTURE.md`**: System architecture docs
- **`docs/database_schema.md`**: DB schema (Hebrew data)

---

## ACTIVE PATTERNS

**Dish Exclusion** (prevents repetition):
```python
exclude_ids = session_manager.get_shown_dishes(user_id)  # Get shown IDs
items = get_menu_items_implementation(..., exclude_ids=exclude_ids)  # Filter
session_manager.add_shown_dishes(user_id, new_dish_ids)  # Track
```

**Category Context Tracking** (maintains category across follow-ups):
```python
# Save category when explicit
if category:
    session_manager.set_last_category(user_id, category)

# Restore category when implicit (follow-up query)
if not category:
    last_category = session_manager.get_last_category(user_id, timeout_minutes=10)
    if last_category:
        category = last_category  # Use saved category

# Clear context when appropriate
session_manager.clear_last_category(user_id)  # On greeting/category list
```

**Context Management**:
```python
history = session_manager.get_history(user_id)  # Last 8 messages
messages = [system_prompt] + history[-8:] + [current_message]
```

---

## KNOWN ISSUES / TODO

None currently active.

---

## TESTING

**Run Tests**:
```powershell
python scripts/test_track_shown.py  # Verify context-aware tracking (5 tests)
python scripts/test_dish_repetition.py  # Verify no repetition
python scripts/test_context_preservation.py  # Verify category tracking (8 tests)
python scripts/test_security.py  # Verify security defenses (26 tests)
python scripts/test_ai_core.py  # Verify database queries
```

---

## DOCUMENTATION POLICY (Updated)

**For AI Agents**: 
-  **Do NOT** append verbose session logs to this file
-  **Do** update "RECENT FIXES" section with significant changes only
-  **Do** focus on coding, not documentation
-  Human will write session summaries at end of work session if needed

**Append Only**:
- New critical bugs fixed
- Architecture changes
- Business rule modifications
- Breaking changes

**Keep Concise**: Max 200 lines total. Remove old fixes when no longer relevant.
