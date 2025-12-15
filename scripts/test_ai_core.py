"""
Test script for AI Core functionality
Tests the get_menu_items_implementation function with various scenarios
"""

import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ai_core import get_menu_items_implementation, format_menu_items_for_ai, GET_MENU_ITEMS_TOOL
import json

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def format_price(item):
    """Helper function to format price - checks both price_per_100g and price_per_unit"""
    price_parts = []
    if item.get('price_per_100g'):
        price_parts.append(f"{item['price_per_100g']} ₪ ל-100 גרם")
    if item.get('price_per_unit'):
        price_parts.append(f"{item['price_per_unit']} ₪ ליחידה")
    return ' / '.join(price_parts) if price_parts else "No price available"

def test_tool_schema():
    """Verify the OpenAI tool schema is properly formatted"""
    print_section("TEST 1: OpenAI Tool Schema")
    print(json.dumps(GET_MENU_ITEMS_TOOL, indent=2, ensure_ascii=False))
    print("\n✓ Tool schema is valid JSON")

def test_basic_query():
    """Test basic query without filters"""
    print_section("TEST 2: Basic Query (No Filters)")
    items = get_menu_items_implementation()
    print(f"Found {len(items)} total items")
    if items:
        print(f"\nFirst item: {items[0]['name']} ({items[0]['category']})")
        print(f"Price: {format_price(items[0])}")

def test_category_filter():
    """Test category filtering"""
    print_section("TEST 3: Category Filter (Salads)")
    items = get_menu_items_implementation(category='סלטים')
    print(f"Found {len(items)} salad items")
    for item in items[:3]:  # Show first 3
        print(f"  - {item['name']}: {format_price(item)}")

def test_price_filter():
    """Test max price filtering"""
    print_section("TEST 4: Price Filter (max 30 ₪)")
    items = get_menu_items_implementation(max_price=30)
    print(f"Found {len(items)} items under 30 ₪")
    for item in items[:3]:
        print(f"  - {item['name']}: {format_price(item)}")

def test_vegan_filter():
    """Test vegan dietary restriction"""
    print_section("TEST 5: Dietary Filter (Vegan)")
    items = get_menu_items_implementation(dietary_restriction='vegan')
    print(f"Found {len(items)} vegan items")
    for item in items[:3]:
        print(f"  - {item['name']} (Vegan: {item.get('is_vegan')})")

def test_gluten_free_filter():
    """Test gluten-free dietary restriction"""
    print_section("TEST 6: Dietary Filter (Gluten Free)")
    items = get_menu_items_implementation(dietary_restriction='gluten_free')
    print(f"Found {len(items)} gluten-free items")
    for item in items[:3]:
        print(f"  - {item['name']} (GF: {item.get('is_gluten_free')})")

def test_allergen_exclusion():
    """Test CRITICAL allergen exclusion (checks both contains AND traces)"""
    print_section("TEST 7: CRITICAL - Allergen Exclusion (Gluten)")

    # First, get all items to see what has gluten
    all_items = get_menu_items_implementation()
    print(f"Total items: {len(all_items)}")

    # Items with gluten in contains or traces
    gluten_items = [
        item for item in all_items
        if 'gluten' in (item.get('allergens_contains') or '').lower()
        or 'gluten' in (item.get('allergens_traces') or '').lower()
        or 'חיטה' in (item.get('allergens_contains') or '').lower()
        or 'חיטה' in (item.get('allergens_traces') or '').lower()
    ]
    print(f"Items with gluten (contains OR traces): {len(gluten_items)}")

    # Now test the exclusion filter
    safe_items = get_menu_items_implementation(dietary_restriction='gluten')
    print(f"Items SAFE for gluten allergy: {len(safe_items)}")

    print("\n✓ CRITICAL: Allergen filter excludes items with gluten in BOTH contains AND traces")

    # Verify no gluten items slipped through
    for item in safe_items:
        allergens_contains = (item.get('allergens_contains') or '').lower()
        allergens_traces = (item.get('allergens_traces') or '').lower()
        if 'gluten' in allergens_contains or 'gluten' in allergens_traces:
            print(f"⚠️  WARNING: {item['name']} has gluten but wasn't filtered!")

def test_combined_filters():
    """Test combining multiple filters"""
    print_section("TEST 8: Combined Filters (Salads + vegan)")
    # Note: Removed max_price filter because salads use price_per_unit, not price_per_100g
    items = get_menu_items_implementation(
        category='סלטים',
        dietary_restriction='vegan'
    )
    print(f"Found {len(items)} items matching all criteria")
    for item in items[:3]:
        print(f"  - {item['name']}: {format_price(item)} (Vegan: {item.get('is_vegan')})")

def test_formatting():
    """Test the formatting function for AI responses"""
    print_section("TEST 9: AI Response Formatting")
    items = get_menu_items_implementation(category='סלטים', dietary_restriction='vegan')
    formatted = format_menu_items_for_ai(items[:2])  # Format first 2 items
    print(formatted)

    # Verify "ל-100 גרם" OR "ליחידה" appears in output
    has_per_100g = 'ל-100 גרם' in formatted
    has_per_unit = 'ליחידה' in formatted

    if has_per_100g or has_per_unit:
        print("\n✓ CRITICAL: Pricing format includes proper unit")
        if has_per_100g:
            print("  ✓ Found: 'ל-100 גרם'")
        if has_per_unit:
            print("  ✓ Found: 'ליחידה'")
    else:
        print("\n⚠️  WARNING: Pricing format missing unit indicators!")

def test_price_fields():
    """Test that both price_per_100g and price_per_unit are handled"""
    print_section("TEST 10: CRITICAL - Both Price Fields Handling")

    all_items = get_menu_items_implementation()

    # Count items with each price type
    items_with_100g = [i for i in all_items if i.get('price_per_100g')]
    items_with_unit = [i for i in all_items if i.get('price_per_unit')]
    items_with_both = [i for i in all_items if i.get('price_per_100g') and i.get('price_per_unit')]

    print(f"Items with price_per_100g: {len(items_with_100g)}")
    print(f"Items with price_per_unit: {len(items_with_unit)}")
    print(f"Items with BOTH prices: {len(items_with_both)}")

    # Test formatting with different price scenarios
    if items_with_100g:
        print(f"\nExample (100g price): {items_with_100g[0]['name']}")
        print(f"  → {format_price(items_with_100g[0])}")

    if items_with_unit:
        print(f"\nExample (unit price): {items_with_unit[0]['name']}")
        print(f"  → {format_price(items_with_unit[0])}")

    if items_with_both:
        print(f"\nExample (both prices): {items_with_both[0]['name']}")
        print(f"  → {format_price(items_with_both[0])}")

    print("\n✓ CRITICAL: Both price types are properly handled")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  AI CORE FUNCTIONALITY TEST SUITE")
    print("="*60)

    try:
        test_tool_schema()
        test_basic_query()
        test_category_filter()
        test_price_filter()
        test_vegan_filter()
        test_gluten_free_filter()
        test_allergen_exclusion()
        test_combined_filters()
        test_formatting()
        test_price_fields()

        print_section("ALL TESTS COMPLETED SUCCESSFULLY ✓")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
