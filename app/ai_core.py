"""
AI Core Module - OpenAI Function Calling Integration

This module defines the OpenAI tool schema and implementation for querying menu items.
Critical: Implements strict allergen checking (both contains AND traces fields).
"""

import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Load system instructions from file
def _load_instructions() -> str:
    """Load system instructions from docs/instructions.txt"""
    instructions_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'docs',
        'instructions.txt'
    )
    try:
        with open(instructions_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Instructions file not found at {instructions_path}")
        return ""

# Cache the instructions at module load time
SYSTEM_INSTRUCTIONS = _load_instructions()

# OpenAI Tool Schema Definitions
GET_BUSINESS_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_business_info",
        "description": "Get the standard business welcome message with hours, services, and links. Use this for greetings like 'היי', 'שלום', 'מה קורה', 'בוקר טוב'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

GET_ORDER_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_order_info",
        "description": "Get information about how to order. Use when user wants to order/purchase: 'אני רוצה להזמין', 'איך מזמינים', 'לקנות'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

GET_CATEGORY_LIST_TOOL = {
    "type": "function",
    "function": {
        "name": "get_category_list",
        "description": "Get the complete list of available menu categories. Use when user asks 'מה יש לכם', 'איזה קטגוריות', 'what do you have'.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

GET_MENU_ITEMS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_menu_items",
        "description": "Query the menu database (ALL DATA IS IN HEBREW). ALWAYS use this tool to answer ANY question about dishes, availability, or menu items. Do NOT answer from memory. Use this for all queries including 'what do you have on [day]?', 'what chicken dishes?', etc. Search terms and parameters should be in HEBREW.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by menu category (IN HEBREW). Available categories: 'סלטים' (salads), 'בשר' (meat), 'עוף' (chicken), 'דגים' (fish), 'סלטי דגים' (fish salads), 'דג מעושן' (smoked fish), 'גבינות' (cheeses), 'ממרחים' (spreads), 'מאפים' (baked goods), 'פשטידות' (pies), 'מרקים' (soups), 'טוגנים' (fried items), 'חמוצים' (pickled), 'תוספות' (sides), 'קינוחים' (desserts), 'קרקרים' (crackers), 'עוגיות' (cookies), 'טבעוני' (vegan), 'ספיישל שישי' (Friday specials), 'ספיישלים שישי' (Friday specials). Leave empty to search all."
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price per 100g in shekels. Only return items at or below this price."
                },
                "dietary_restriction": {
                    "type": "string",
                    "description": "Dietary filter (use English keys). Options: 'vegan' (טבעוני), 'gluten_free' (ללא גלוטן), or allergen to EXCLUDE: 'gluten' (גלוטן), 'nuts' (אגוזים), 'dairy' (חלב), 'eggs' (ביצים), 'sesame' (שומשום), 'soy' (סויה), 'celery' (סלרי), 'mustard' (חרדל), 'fish' (דגים). CRITICAL: Items are excluded if they contain OR may contain traces. IMPORTANT: If user says 'אני רגיש ל' (I'm sensitive to), 'יש לי אלרגיה ל' (I have allergy to), 'אני אלרגי ל' (I'm allergic to), or 'לא יכול/ה לאכול' (can't eat) followed by an allergen, use that allergen's EXCLUSION filter (e.g., 'gluten', 'nuts', etc.), NOT 'gluten_free' or 'vegan'.",
                    "enum": ["vegan", "gluten_free", "gluten", "nuts", "dairy", "eggs", "sesame", "soy", "celery", "mustard", "fish", ""]
                },
                "search_term": {
                    "type": "string",
                    "description": "Free text search for item name or description IN HEBREW. Example: 'פלאפל' or 'חומוס'. Use for finding specific dishes."
                },
                "availability_day": {
                    "type": "string",
                    "description": "Filter by day of week (IN HEBREW). Use when customer asks 'what's available on [day]?'. Hebrew days: 'א' (Sunday/ראשון), 'ב' (Monday/שני), 'ג' (Tuesday/שלישי), 'ד' (Wednesday/רביעי), 'ה' (Thursday/חמישי), 'ו' (Friday/שישי). Items with this letter in availability_days will be returned.",
                    "enum": ["א", "ב", "ג", "ד", "ה", "ו", ""]
                }
            },
            "required": []
        }
    }
}


def get_menu_items_implementation(
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    dietary_restriction: Optional[str] = None,
    search_term: Optional[str] = None,
    exclude_ids: Optional[List[int]] = None,
    availability_day: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Implementation function that queries Supabase for menu items.

    Args:
        category: Filter by category (e.g., 'Breads', 'Meat', 'Salads')
        max_price: Maximum price per 100g (filters price_per_100g)
        dietary_restriction: Either 'vegan', 'gluten_free', or an allergen to EXCLUDE
        search_term: Text to search in name or description
        exclude_ids: List of dish IDs to exclude (for variety - already shown dishes)
        availability_day: Hebrew day letter to filter by (א, ב, ג, ד, ה, ו)

    Returns:
        List of menu item dictionaries

    Critical Business Rules:
        - ALLERGEN SAFETY: When excluding an allergen, check BOTH allergens_contains
          AND allergens_traces fields. If EITHER contains the allergen, exclude the item.
        - All prices are per 100g (price_per_100g field)
    """

    # Start building the query
    query = supabase.table('menu_items').select('*')

    # Filter by category if provided
    if category and category.strip():
        query = query.eq('category', category)

    # Filter by max price if provided
    if max_price is not None:
        query = query.lte('price_per_100g', max_price)

    # Handle dietary restrictions
    if dietary_restriction and dietary_restriction.strip():
        restriction = dietary_restriction.lower().strip()

        if restriction == 'vegan':
            # Filter for vegan items
            query = query.eq('is_vegan', True)

        elif restriction == 'gluten_free':
            # Filter for gluten-free items
            query = query.eq('is_gluten_free', True)

        else:
            # Treat as allergen exclusion - CRITICAL SAFETY RULE
            # Must check BOTH allergens_contains AND allergens_traces
            # We need to fetch all items and filter in Python because Supabase
            # doesn't support complex OR conditions with ILIKE on multiple columns
            pass  # Will handle after query execution

    # Handle search term (case-insensitive search in name or description)
    if search_term and search_term.strip():
        # Note: Supabase postgrest uses 'ilike' for case-insensitive search
        # For OR conditions with ilike, we need to use .or_() method
        query = query.or_(f'name.ilike.%{search_term}%,description.ilike.%{search_term}%')

    # Handle availability_day filter (filter by Hebrew day letter)
    if availability_day and availability_day.strip():
        # Filter items that have this day letter in their availability_days field
        query = query.ilike('availability_days', f'%{availability_day}%')

    # Execute query with higher limit to account for filtering
    try:
        # Request more items than needed to account for exclusions
        fetch_limit = 15 if exclude_ids else 5
        response = query.limit(fetch_limit).execute()
        items = response.data

        # Post-processing: Exclude already shown dishes (for variety)
        if exclude_ids:
            items = [item for item in items if item.get('id') not in exclude_ids]

        # Post-processing for allergen exclusions (CRITICAL SAFETY)
        if dietary_restriction and dietary_restriction.strip():
            restriction = dietary_restriction.lower().strip()

            # If it's not vegan or gluten_free, treat as allergen exclusion
            if restriction not in ['vegan', 'gluten_free']:
                items = _filter_allergen_exclusion(items, restriction)

        # RETRY MECHANISM: If no results and category was used, try alternative strategies
        if not items and category and category.strip():
            items = _retry_query_with_fallbacks(
                category=category,
                max_price=max_price,
                dietary_restriction=dietary_restriction,
                search_term=search_term,
                exclude_ids=exclude_ids,
                availability_day=availability_day
            )

        # Final limit to 5 items
        return items[:5]

    except Exception as e:
        print(f"Database query error: {e}")
        return []


def get_category_total_count(
    category: Optional[str] = None,
    dietary_restriction: Optional[str] = None,
    availability_day: Optional[str] = None
) -> int:
    """
    Get total count of dishes in a category (for counter display)

    Args:
        category: Category to count
        dietary_restriction: Dietary filter
        availability_day: Availability filter

    Returns:
        Total number of dishes matching criteria
    """
    query = supabase.table('menu_items').select('id', count='exact')

    if category and category.strip():
        query = query.eq('category', category)

    if dietary_restriction and dietary_restriction.strip():
        restriction = dietary_restriction.lower().strip()
        if restriction == 'vegan':
            query = query.eq('is_vegan', True)
        elif restriction == 'gluten_free':
            query = query.eq('is_gluten_free', True)

    if availability_day and availability_day.strip():
        query = query.ilike('availability_days', f'%{availability_day}%')

    try:
        response = query.execute()
        return response.count if hasattr(response, 'count') else len(response.data)
    except Exception as e:
        print(f"Count query error: {e}")
        return 0


def _retry_query_with_fallbacks(
    category: str,
    max_price: Optional[float] = None,
    dietary_restriction: Optional[str] = None,
    search_term: Optional[str] = None,
    exclude_ids: Optional[List[int]] = None,
    availability_day: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retry query with fallback strategies when category query returns empty results.

    Strategies:
    1. Try search_term instead of category (handles spelling variations)
    2. Try alternative category spellings (e.g., 'ספיישל שישי' vs 'ספיישלים שישי')
    3. Try fuzzy category match (partial match)

    Args:
        category: Original category that failed
        max_price, dietary_restriction, search_term, exclude_ids, availability_day: Original params

    Returns:
        List of menu items from retry attempt
    """

    # Strategy 1: Use category as search_term instead (searches name + description)
    query = supabase.table('menu_items').select('*')
    query = query.or_(f'name.ilike.%{category}%,description.ilike.%{category}%,category.ilike.%{category}%')

    if max_price is not None:
        query = query.lte('price_per_100g', max_price)

    if availability_day and availability_day.strip():
        query = query.ilike('availability_days', f'%{availability_day}%')

    try:
        response = query.limit(15).execute()
        items = response.data

        if exclude_ids:
            items = [item for item in items if item.get('id') not in exclude_ids]

        if dietary_restriction and dietary_restriction.strip():
            restriction = dietary_restriction.lower().strip()
            if restriction == 'vegan':
                items = [item for item in items if item.get('is_vegan')]
            elif restriction == 'gluten_free':
                items = [item for item in items if item.get('is_gluten_free')]
            elif restriction not in ['vegan', 'gluten_free']:
                items = _filter_allergen_exclusion(items, restriction)

        if items:
            print(f"Retry successful: Found {len(items)} items using fuzzy search for category '{category}'")
            return items

        # Strategy 2: Try alternative spellings for common categories
        category_alternatives = {
            'ספיישל שישי': ['ספיישלים שישי', 'ספיישל יום שישי', 'שישי'],
            'ספיישלים שישי': ['ספיישל שישי', 'ספיישל יום שישי', 'שישי'],
        }

        if category in category_alternatives:
            for alt_category in category_alternatives[category]:
                query = supabase.table('menu_items').select('*').eq('category', alt_category)

                if max_price is not None:
                    query = query.lte('price_per_100g', max_price)

                if availability_day and availability_day.strip():
                    query = query.ilike('availability_days', f'%{availability_day}%')

                response = query.limit(15).execute()
                items = response.data

                if exclude_ids:
                    items = [item for item in items if item.get('id') not in exclude_ids]

                if dietary_restriction and dietary_restriction.strip():
                    restriction = dietary_restriction.lower().strip()
                    if restriction == 'vegan':
                        items = [item for item in items if item.get('is_vegan')]
                    elif restriction == 'gluten_free':
                        items = [item for item in items if item.get('is_gluten_free')]
                    elif restriction not in ['vegan', 'gluten_free']:
                        items = _filter_allergen_exclusion(items, restriction)

                if items:
                    print(f"Retry successful: Found {len(items)} items using alternative spelling '{alt_category}'")
                    return items

        return []

    except Exception as e:
        print(f"Retry query error: {e}")
        return []


def _filter_allergen_exclusion(items: List[Dict[str, Any]], allergen: str) -> List[Dict[str, Any]]:
    """
    Filter out items that contain or may contain traces of the specified allergen.

    CRITICAL SAFETY RULE: Check BOTH allergens_contains AND allergens_traces.
    If EITHER field mentions the allergen, the item is UNSAFE and must be excluded.

    Args:
        items: List of menu items from database
        allergen: Allergen to exclude (e.g., 'nuts', 'gluten', 'dairy')

    Returns:
        Filtered list with unsafe items removed
    """
    safe_items = []
    allergen_lower = allergen.lower()

    # Common allergen variations to check (English keys → Hebrew DB values)
    allergen_patterns = {
        'gluten': ['gluten', 'wheat', 'חיטה', 'גלוטן', 'קמח'],
        'nuts': ['nuts', 'peanuts', 'אגוזים', 'בוטנים', 'שקדים', 'almond', 'cashew', 'walnut'],
        'dairy': ['dairy', 'milk', 'חלב', 'cheese', 'גבינה', 'cream', 'butter', 'חמאה'],
        'eggs': ['eggs', 'ביצים', 'egg'],
        'sesame': ['sesame', 'שומשום', 'tahini', 'טחינה'],
        'soy': ['soy', 'סויה', 'soya'],
        'celery': ['celery', 'סלרי'],
        'mustard': ['mustard', 'חרדל'],
        'fish': ['fish', 'דגים', 'דג']
    }

    # Get patterns for this allergen, default to just the allergen itself
    patterns = allergen_patterns.get(allergen_lower, [allergen_lower])

    for item in items:
        allergens_contains = (item.get('allergens_contains') or '').lower()
        allergens_traces = (item.get('allergens_traces') or '').lower()

        # Check if ANY pattern matches in EITHER field
        is_unsafe = False
        for pattern in patterns:
            if pattern in allergens_contains or pattern in allergens_traces:
                is_unsafe = True
                break

        # Only include if safe (allergen not found in either field)
        if not is_unsafe:
            safe_items.append(item)

    return safe_items


def format_menu_items_for_ai(items: List[Dict[str, Any]]) -> str:
    """
    Format menu items into a COMPRESSED string for the AI to process.
    OPTIMIZED for token efficiency while keeping critical safety info.

    Args:
        items: List of menu item dictionaries

    Returns:
        Formatted string describing the menu items (compressed format)
    """
    if not items:
        return "לא נמצאו פריטים תואמים בתפריט."

    formatted_lines = []
    for item in items:
        parts = []

        # Name
        parts.append(item['name'])

        # Price - CRITICAL: Include correct unit (ל-100 גרם or ליחידה)
        price_parts = []
        if item.get('price_per_100g'):
            price_parts.append(f"{item['price_per_100g']}₪/100g")
        if item.get('price_per_unit'):
            price_parts.append(f"{item['price_per_unit']}₪/יח")
        if price_parts:
            parts.append(' '.join(price_parts))

        # Dietary flags (compact)
        flags = []
        if item.get('is_vegan'):
            flags.append('🌱')
        if item.get('is_gluten_free'):
            flags.append('ללא גלוטן')
        if flags:
            parts.append(' '.join(flags))

        # Allergens - CRITICAL SAFETY INFO (must include both fields)
        allergen_info = []
        if item.get('allergens_contains'):
            allergen_info.append(f"⚠️{item['allergens_contains']}")
        if item.get('allergens_traces'):
            allergen_info.append(f"⚠️עקבות:{item['allergens_traces']}")
        if allergen_info:
            parts.append(' '.join(allergen_info))

        # Availability (compact)
        if item.get('availability_days'):
            parts.append(f"📅{item['availability_days']}")

        # Package type (compact)
        if item.get('package_type'):
            parts.append(f"📦{item['package_type']}")

        # Combine all parts with separator
        formatted_lines.append(' | '.join(parts))

    return '\n\n'.join(formatted_lines)


def prepare_user_message_with_instructions(user_message: str) -> str:
    """
    Append system instructions to the user message.

    This ensures GPT-4o-mini receives the critical business rules
    (pricing format, allergen safety, etc.) with every request.

    Args:
        user_message: The original message from the user

    Returns:
        Combined message with instructions appended
    """
    if not SYSTEM_INSTRUCTIONS:
        return user_message

    # Append instructions as a compact system context block (OPTIMIZED)
    return f"""{user_message}

[RULES: {SYSTEM_INSTRUCTIONS}]"""


# Export the tool schema and implementation
__all__ = [
    'GET_MENU_ITEMS_TOOL',
    'get_menu_items_implementation',
    'format_menu_items_for_ai',
    'prepare_user_message_with_instructions',
    'SYSTEM_INSTRUCTIONS',
    'supabase'
]
