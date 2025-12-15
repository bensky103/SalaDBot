"""
AI Core Module - OpenAI Function Calling Integration

This module defines the OpenAI tool schema and implementation for querying menu items.
Critical: Implements strict allergen checking (both contains AND traces fields).
"""

import os
import logging
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from app.config import Config

logger = logging.getLogger(Config.LOGGER_NAME)

# Initialize Supabase client
supabase: Client = create_client(
    Config.SUPABASE_URL,
    Config.SUPABASE_KEY
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
        logger.warning(f"{{_load_instructions}} Instructions file not found at {instructions_path}")
        return ""

# Cache the instructions at module load time
SYSTEM_INSTRUCTIONS = _load_instructions()

# OpenAI Tool Schema Definitions
GET_BUSINESS_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_business_info",
        "description": "Business welcome message. Use for greetings.",
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
        "description": "Order information. Use when user wants to order.",
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
        "description": "List all menu categories.",
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
        "description": "Query menu database. ALL data in HEBREW. Use for dishes, availability, allergens.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category in HEBREW: סלטים, בשר, עוף, דגים, גבינות, ממרחים, מאפים, פשטידות, מרקים, קינוחים, עוגיות, קרקרים, טבעוני, etc. CRITICAL: עוגיות and קינוחים are DIFFERENT categories!"
                },
                "max_price": {
                    "type": "number",
                    "description": "Max price per 100g (shekels)."
                },
                "dietary_restriction": {
                    "type": "string",
                    "description": "Filter: vegan, gluten_free, OR allergen to EXCLUDE: gluten, nuts, dairy, eggs, sesame, soy, celery, mustard, fish.",
                    "enum": ["vegan", "gluten_free", "gluten", "nuts", "dairy", "eggs", "sesame", "soy", "celery", "mustard", "fish", ""]
                },
                "search_term": {
                    "type": "string",
                    "description": "Search term in HEBREW."
                },
                "availability_day": {
                    "type": "string",
                    "description": "Day: א (Sun), ב (Mon), ג (Tue), ד (Wed), ה (Thu), ו (Fri).",
                    "enum": ["א", "ב", "ג", "ד", "ה", "ו", ""]
                },
                "track_shown": {
                    "type": "boolean",
                    "description": "TRUE=browsing (minimal), FALSE=details (full info). Default: true."
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
        fetch_limit = Config.DB_FETCH_LIMIT_WITH_EXCLUSIONS if exclude_ids else Config.DB_FETCH_LIMIT_NO_EXCLUSIONS
        response = query.limit(fetch_limit).execute()
        items = response.data

        # Post-processing: Exclude already shown dishes (for variety)
        if exclude_ids:
            items = [item for item in items if item.get('id') not in exclude_ids]

        # Post-processing for dietary restrictions (CRITICAL SAFETY)
        items = _apply_dietary_filters(items, dietary_restriction)

        # RETRY MECHANISM: If no results and category was used, try fuzzy search
        # BUT: Do NOT retry if we had exclude_ids (items already shown - category exhausted)
        if not items and category and category.strip() and not exclude_ids:
            items = _retry_query_with_fallbacks(
                category=category,
                max_price=max_price,
                dietary_restriction=dietary_restriction,
                exclude_ids=exclude_ids,
                availability_day=availability_day
            )

        # Final limit to configured max dishes
        return items[:Config.MAX_DISHES_RETURNED]

    except Exception as e:
        logger.error(f"{{get_menu_items_implementation}} Database query error: {e}", exc_info=True)
        return []


def _retry_query_with_fallbacks(
    category: str,
    max_price: Optional[float] = None,
    dietary_restriction: Optional[str] = None,
    exclude_ids: Optional[List[int]] = None,
    availability_day: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retry query with fuzzy search when category query returns empty results.

    Strategy: Use category as search term (searches name + description + category fields)

    Args:
        category: Original category that failed
        max_price, dietary_restriction, exclude_ids, availability_day: Original params

    Returns:
        List of menu items from retry attempt
    """

    # Use category as fuzzy search term (searches name + description + category)
    query = supabase.table('menu_items').select('*')
    query = query.or_(f'name.ilike.%{category}%,description.ilike.%{category}%,category.ilike.%{category}%')

    if max_price is not None:
        query = query.lte('price_per_100g', max_price)

    if availability_day and availability_day.strip():
        query = query.ilike('availability_days', f'%{availability_day}%')

    try:
        response = query.limit(Config.DB_FETCH_LIMIT_WITH_EXCLUSIONS).execute()
        items = response.data

        if exclude_ids:
            items = [item for item in items if item.get('id') not in exclude_ids]

        items = _apply_dietary_filters(items, dietary_restriction)

        if items:
            logger.info(f"{{_retry_query_with_fallbacks}} Retry successful: Found {len(items)} items for category '{category}'")
            return items

        return []

    except Exception as e:
        logger.error(f"{{_retry_query_with_fallbacks}} Retry query failed: {e}", exc_info=True)
        return []


def _apply_dietary_filters(items: List[Dict[str, Any]], dietary_restriction: Optional[str]) -> List[Dict[str, Any]]:
    """
    Apply dietary restriction filters to items (vegan, gluten_free, or allergen exclusion).

    Args:
        items: List of menu items from database
        dietary_restriction: 'vegan', 'gluten_free', or allergen to exclude

    Returns:
        Filtered list of items
    """
    if not dietary_restriction or not dietary_restriction.strip():
        return items

    restriction = dietary_restriction.lower().strip()

    if restriction == 'vegan':
        return [item for item in items if item.get('is_vegan')]
    elif restriction == 'gluten_free':
        return [item for item in items if item.get('is_gluten_free')]
    else:
        # Allergen exclusion
        return _filter_allergen_exclusion(items, restriction)


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


def format_menu_items_for_ai(items: List[Dict[str, Any]], all_shown: bool = False, no_results: bool = False, include_details: bool = False) -> str:
    """
    Format menu items into a string for the AI to process.

    By default (include_details=False): Returns ONLY dish name, price, and package type (minimal browsing view)
    When include_details=True: Returns full details including allergens, availability, dietary flags, ingredients

    Args:
        items: List of menu item dictionaries
        all_shown: If True, indicates all matching items were already shown (browsing exhaustion)
        no_results: If True, indicates query returned 0 results (legitimately empty)
        include_details: If True, include allergens, availability, dietary flags, ingredients (for detail queries)

    Returns:
        Formatted string describing the menu items
    """
    if not items:
        if all_shown:
            return "[ALL_DISHES_SHOWN] כל המנות בקטגוריה זו כבר הוצגו."
        if no_results:
            return "[NO_RESULTS] לא נמצאו מנות התואמות את הקריטריונים."
        return "לא נמצאו פריטים תואמים בתפריט."

    # Add mode tag to help AI understand formatting requirements
    mode_tag = "[D]" if include_details else "[B]"
    format_instruction = "Full details" if include_details else "Name, price, package only"

    logger.debug(f"{{format_menu_items_for_ai}} Formatting {len(items)} items | Mode: {mode_tag} | Details: {include_details}")
    
    # CRITICAL: For detail mode with ONE item, use natural language format to prevent data mixing
    if include_details and len(items) == 1:
        item = items[0]
        response_parts = []
        
        # Dish name header
        response_parts.append(f"=== {item['name']} ===\n")
        
        # Price
        if item.get('price_per_100g'):
            response_parts.append(f"💰 מחיר: {item['price_per_100g']}₪ ל-100 גרם")
        if item.get('price_per_unit'):
            response_parts.append(f"💰 מחיר: {item['price_per_unit']}₪ ליחידה")
        
        # Package
        if item.get('package_type'):
            response_parts.append(f"📦 אריזה: {item['package_type']}")
        
        # Ingredients (CRITICAL)
        if item.get('description'):
            response_parts.append(f"\n🥘 {item['description']}")
        
        # Allergens (CRITICAL)
        if item.get('allergens_contains'):
            response_parts.append(f"\n⚠️ מכילה: {item['allergens_contains']}")
        if item.get('allergens_traces'):
            response_parts.append(f"⚠️ עלולה להכיל עקבות של: {item['allergens_traces']}")
        
        # Availability
        if item.get('availability_days'):
            response_parts.append(f"\n📅 זמינות: {item['availability_days']}")
        
        return '\n'.join(response_parts)
    
    # Original format for browsing or multiple items
    formatted_lines = [f"{mode_tag} {format_instruction}\n"]
    
    for idx, item in enumerate(items, 1):
        parts = []
        
        # CRITICAL: Add dish number and clear separator for multiple dishes
        if len(items) > 1:
            parts.append(f"[DISH #{idx}]")

        # Name (always included)
        parts.append(item['name'])

        # Price - CRITICAL: Include correct unit (ל-100 גרם or ליחידה) (always included)
        price_parts = []
        if item.get('price_per_100g'):
            price_parts.append(f"{item['price_per_100g']}₪/100g")
        if item.get('price_per_unit'):
            price_parts.append(f"{item['price_per_unit']}₪/יח")
        if price_parts:
            parts.append(' '.join(price_parts))

        # Package type - always show if available (helps identify unit size)
        if item.get('package_type'):
            parts.append(f"📦{item['package_type']}")

        # DETAILED INFO - Only include when explicitly requested (include_details=True)
        if include_details:
            # Dietary flags
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

            # Availability
            if item.get('availability_days'):
                parts.append(f"📅{item['availability_days']}")

            # Description (ingredients) - CRITICAL for ingredient queries
            if item.get('description'):
                parts.append(item['description'])

        # Combine all parts with separator
        dish_line = ' | '.join(parts)
        
        # Add explicit separator between dishes for clarity
        if len(items) > 1:
            dish_line = f"--- {dish_line} ---"
        
        formatted_lines.append(dish_line)

    return '\n\n'.join(formatted_lines)


# Export the tool schema and implementation
__all__ = [
    'GET_MENU_ITEMS_TOOL',
    'GET_BUSINESS_INFO_TOOL',
    'GET_ORDER_INFO_TOOL',
    'GET_CATEGORY_LIST_TOOL',
    'get_menu_items_implementation',
    'format_menu_items_for_ai',
    'SYSTEM_INSTRUCTIONS',
    'supabase'
]
