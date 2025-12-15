"""
Test ingredient extraction and formatting to prevent LLM hallucination.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai_core import format_menu_items_for_ai

# Test data matching the actual database entry
test_item = {
    'id': 1,
    'name': 'פשטידת בטטה חלבי',
    'description': 'רכיבים:בטטה, ביצים, פירורי לחם, שמנת חלבית, אבקת מרק, שמן סויה, שום, תבלינים',
    'price_per_unit': 55.0,
    'package_type': 'עגולה גדולה',
    'allergens_contains': 'ביצים, סויה, סלרי, חלב, גלוטן',
    'allergens_traces': 'גלוטן, בוטנים,אגוזים, ביצים, סויה, דגים, שומשום, חרדל וסלרי',
    'availability_days': 'ימים ג - ו'
}

print("=" * 80)
print("TEST: Single dish with ingredients (detail mode)")
print("=" * 80)

result = format_menu_items_for_ai([test_item], include_details=True)
print(result)

print("\n" + "=" * 80)
print("EXPECTED INGREDIENTS:")
print("בטטה, ביצים, פירורי לחם, שמנת חלבית, אבקת מרק, שמן סויה, שום, תבלינים")
print("=" * 80)

# Check if ingredients are extracted correctly
if 'פירורי לחם' in result:
    print("✅ PASS: 'פירורי לחם' found in output")
else:
    print("❌ FAIL: 'פירורי לחם' NOT found in output")

if 'שום' in result:
    print("✅ PASS: 'שום' found in output")
else:
    print("❌ FAIL: 'שום' NOT found in output")

if 'פירות יבשים' not in result:
    print("✅ PASS: No hallucinated 'פירות יבשים'")
else:
    print("❌ FAIL: Hallucinated ingredient 'פירות יבשים' found!")

# Test multiple dishes
print("\n\n" + "=" * 80)
print("TEST: Multiple dishes with ingredients")
print("=" * 80)

test_items = [
    {
        'id': 1,
        'name': 'פשטידת בטטה חלבי',
        'description': 'רכיבים:בטטה, ביצים, פירורי לחם, שמנת חלבית, אבקת מרק, שמן סויה, שום, תבלינים',
        'price_per_unit': 55.0,
        'allergens_contains': 'ביצים, סויה, סלרי, חלב, גלוטן',
    },
    {
        'id': 2,
        'name': 'פשטידת ברוקלי חלבית',
        'description': 'רכיבים: ברוקולי, ביצים, שמנת חלבית, אבקת מרק, שום, תבלינים',
        'price_per_unit': 55.0,
        'allergens_contains': 'ביצים, סלרי, חלב',
    }
]

result_multi = format_menu_items_for_ai(test_items, include_details=True)
print(result_multi)

print("\n" + "=" * 80)
print("VERIFICATION:")
if '[DISH #1]' in result_multi and '[DISH #2]' in result_multi:
    print("✅ PASS: Dishes are numbered correctly")
else:
    print("❌ FAIL: Dish numbering missing")

if 'בטטה' in result_multi and 'ברוקולי' in result_multi:
    print("✅ PASS: Both dishes have their unique first ingredients")
else:
    print("❌ FAIL: Ingredients are mixed or missing")
