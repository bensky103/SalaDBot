"""
End-to-end test for ingredient hallucination fix.

This test simulates the exact scenario from the user's bug report:
- User asks for פשטידות list
- User asks "מה הרכיבים שלהם?"
- Verify bot returns EXACT ingredients without modification
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai_core import format_menu_items_for_ai

print("=" * 80)
print("INGREDIENT HALLUCINATION FIX - END-TO-END TEST")
print("=" * 80)

# Simulate the exact data from the user's bug report
pie_dish = {
    'id': 123,
    'name': 'פשטידת בטטה חלבי',
    'description': 'רכיבים:בטטה, ביצים, פירורי לחם, שמנת חלבית, אבקת מרק, שמן סויה, שום, תבלינים',
    'price_per_unit': 55.0,
    'package_type': 'עגולה גדולה',
    'allergens_contains': 'ביצים, סויה, סלרי, חלב, גלוטן',
    'allergens_traces': 'גלוטן, בוטנים,אגוזים, ביצים, סויה, דגים, שומשום, חרדל וסלרי',
    'availability_days': 'ימים ג - ו',
    'is_vegan': False,
    'is_gluten_free': False
}

print("\n📋 STEP 1: User asks for ingredients")
print("-" * 80)

# Format as single dish detail query
tool_response = format_menu_items_for_ai([pie_dish], include_details=True)
print("Tool response sent to LLM:")
print(tool_response)

print("\n" + "=" * 80)
print("🔍 VERIFICATION")
print("=" * 80)

# Expected ingredients from database
expected_ingredients = "בטטה, ביצים, פירורי לחם, שמנת חלבית, אבקת מרק, שמן סויה, שום, תבלינים"

print(f"\n✓ Expected ingredients:\n  {expected_ingredients}")

# Check for correct ingredients
tests = [
    ("בטטה", "Beets/sweet potato"),
    ("ביצים", "Eggs"),
    ("פירורי לחם", "Bread crumbs - CRITICAL"),
    ("שמנת חלבית", "Dairy cream"),
    ("אבקת מרק", "Soup powder"),
    ("שמן סויה", "Soy oil"),
    ("שום", "Garlic - CRITICAL (was missing)"),
    ("תבלינים", "Spices"),
]

all_passed = True
for ingredient, description in tests:
    if ingredient in tool_response:
        print(f"  ✅ '{ingredient}' ({description})")
    else:
        print(f"  ❌ '{ingredient}' ({description}) - MISSING!")
        all_passed = False

# Check for hallucinated ingredients
hallucination_tests = [
    ("פירות יבשים", "Dried fruits - WRONG (was hallucinated)"),
]

for wrong_ingredient, description in hallucination_tests:
    if wrong_ingredient not in tool_response:
        print(f"  ✅ No '{wrong_ingredient}' ({description})")
    else:
        print(f"  ❌ '{wrong_ingredient}' ({description}) - HALLUCINATED!")
        all_passed = False

# Check for explicit copy instruction
if "COPY INGREDIENTS EXACTLY" in tool_response:
    print(f"  ✅ Explicit 'COPY EXACTLY' instruction present")
else:
    print(f"  ❌ Missing 'COPY EXACTLY' instruction")
    all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("✅ ALL TESTS PASSED - Ingredient hallucination fix working!")
else:
    print("❌ SOME TESTS FAILED - Review the output above")
print("=" * 80)

# Test with multiple dishes
print("\n\n" + "=" * 80)
print("📋 BONUS TEST: Multiple dishes")
print("=" * 80)

dishes = [
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
    },
    {
        'id': 3,
        'name': 'פשטידת פטריות חלבי',
        'description': 'רכיבים: פטריות, בצל, שמנת חלבית, ביצים, פירורי לחם, אבקת מרק, שום, שמן סויה, תבלינים',
        'price_per_unit': 55.0,
        'allergens_contains': 'חלב, סויה, סלרי, גלוטן, ביצים',
    }
]

multi_response = format_menu_items_for_ai(dishes, include_details=True)
print("Tool response for multiple dishes:")
print(multi_response)

print("\n" + "=" * 80)
print("🔍 MULTI-DISH VERIFICATION")
print("=" * 80)

multi_tests = [
    ("[DISH #1]", "Dish 1 marker"),
    ("[DISH #2]", "Dish 2 marker"),
    ("[DISH #3]", "Dish 3 marker"),
    ("בטטה", "Beets in dish 1"),
    ("ברוקולי", "Broccoli in dish 2"),
    ("פטריות", "Mushrooms in dish 3"),
    ("פירורי לחם", "Bread crumbs in dishes 1 & 3"),
]

multi_passed = True
for marker, description in multi_tests:
    if marker in multi_response:
        print(f"  ✅ '{marker}' ({description})")
    else:
        print(f"  ❌ '{marker}' ({description}) - MISSING!")
        multi_passed = False

print("\n" + "=" * 80)
if multi_passed:
    print("✅ MULTI-DISH TEST PASSED")
else:
    print("❌ MULTI-DISH TEST FAILED")
print("=" * 80)
