"""
Test script for multiple ingredient queries
Tests that bot returns DIFFERENT ingredients for DIFFERENT dishes
"""

import asyncio
import sys
import os
import io

# Fix Windows console encoding for Hebrew
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat_service import ChatService


async def test_multiple_ingredient_query():
    """
    Test Case: User asks for ingredients of multiple dishes
    Expected: Bot should return DIFFERENT ingredients for each dish
    """
    print("=" * 80)
    print("TEST: Multiple Ingredient Query")
    print("=" * 80)

    chat_service = ChatService()
    user_id = "test_multiple_ingredients"

    # Step 1: Greet
    print("\n[User]: היי")
    response1 = await chat_service.process_user_message("היי", user_id, reset_history=True)
    print(f"[Bot]: {response1[:100]}...")

    # Step 2: Ask for cookies
    print("\n[User]: איזה עוגיות יש לכם?")
    response2 = await chat_service.process_user_message("איזה עוגיות יש לכם?", user_id)
    print(f"[Bot]: {response2}")

    # Step 3: Ask for ingredients of all shown dishes
    print("\n[User]: מה הרכיבים של המנות שהראת לי?")
    response3 = await chat_service.process_user_message("מה הרכיבים של המנות שהראת לי?", user_id)
    print(f"[Bot]: {response3}")

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION:")
    print("=" * 80)

    # Check that response contains all three dish names
    expected_dishes = ["מגולגלות תמרים", "מגולגלות נוטלה", "עוגיות גרנולה"]
    found_dishes = [dish for dish in expected_dishes if dish in response3]

    print(f"\n✓ Expected dishes: {expected_dishes}")
    print(f"✓ Found dishes: {found_dishes}")

    # Check that each dish has unique ingredients
    has_תמרים = "תמרים" in response3
    has_נוטלה = "נוטלה" in response3 or "שוקולד" in response3
    has_שיבולת = "שיבולת" in response3 or "חמוציות" in response3

    print(f"\n✓ Contains תמרים (unique to מגולגלות תמרים): {has_תמרים}")
    print(f"✓ Contains נוטלה/שוקולד (unique to מגולגלות נוטלה): {has_נוטלה}")
    print(f"✓ Contains שיבולת/חמוציות (unique to גרנולה): {has_שיבולת}")

    # Check that response doesn't repeat the same ingredients for all dishes
    lines = response3.split('\n')
    ingredient_lines = [line for line in lines if 'מכיל' in line or 'רכיבים' in line]

    print(f"\n✓ Ingredient lines found: {len(ingredient_lines)}")
    if len(ingredient_lines) >= 3:
        print("✓ Found separate ingredient lists for each dish")

        # Check that they're not identical
        unique_lines = set(ingredient_lines)
        if len(unique_lines) >= 3:
            print("✅ PASS: Each dish has DIFFERENT ingredients!")
        else:
            print("❌ FAIL: Some dishes have identical ingredient lists (copy-paste error)")
            print(f"   Unique lines: {len(unique_lines)} (expected: 3)")
    else:
        print(f"❌ FAIL: Expected 3 ingredient lines, found {len(ingredient_lines)}")

    # Final result
    success = (
        len(found_dishes) == 3 and
        has_תמרים and has_נוטלה and has_שיבולת and
        len(ingredient_lines) >= 3
    )

    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED: Bot correctly returned different ingredients for each dish")
    else:
        print("❌ TEST FAILED: Bot did not return correct ingredients")
    print("=" * 80)

    return success


if __name__ == "__main__":
    result = asyncio.run(test_multiple_ingredient_query())
    sys.exit(0 if result else 1)
