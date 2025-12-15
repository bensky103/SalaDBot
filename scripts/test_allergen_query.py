"""
Test script for allergen query fix
Verifies that bot correctly returns allergens when asked
"""

import sys
import os
import asyncio
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix Windows console encoding for Hebrew
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chat_service import ChatService


async def test_allergen_query():
    """
    Test: User asks for allergens of multiple dishes
    Expected: Bot returns allergen information for each dish separately
    """
    print("=" * 80)
    print("TEST: Multiple Allergen Query")
    print("=" * 80)

    service = ChatService()
    test_user = "test_allergen"

    # Step 1: Ask for פשטידות
    print("\n[User]: איזה פשטידות יש לכם?")
    response1 = await service.process_user_message(
        "איזה פשטידות יש לכם?",
        user_id=test_user,
        reset_history=True
    )
    print(f"[Bot]: {response1}\n")

    # Step 2: Ask for allergens
    print("[User]: מה האלרגנים של הפשטידות שציינת?")
    response2 = await service.process_user_message(
        "מה האלרגנים של הפשטידות שציינת?",
        user_id=test_user,
        reset_history=False
    )
    print(f"[Bot]: {response2}\n")

    print("=" * 80)
    print("VALIDATION:")
    print("=" * 80)

    # Verify response contains allergen information
    allergen_keywords = ["מכילה", "עקבות", "ביצים", "חלב", "גלוטן", "סלרי"]
    has_allergen_info = any(keyword in response2 for keyword in allergen_keywords)
    
    # Should NOT contain ingredient descriptions (actual food items like בטטה, ברוקולי in ingredient lists)
    # Allergens use "מכילה: [allergen], [allergen]" format
    # Ingredients use "מכילה: [ingredient], [ingredient]" with actual food items
    has_ingredient_info = ("בטטה," in response2 or "ברוקולי," in response2 or "פטריות," in response2)
    
    # Should mention multiple dishes
    dish_names = ["פשטידת בטטה", "פשטידת ברוקלי", "פשטידת פטריות", "פשטידת ירקות"]
    dishes_found = sum(1 for dish in dish_names if dish in response2)
    
    print(f"{'✅' if has_allergen_info else '❌'} Contains allergen information: {has_allergen_info}")
    print(f"{'✅' if not has_ingredient_info else '❌'} Does NOT contain ingredients: {not has_ingredient_info}")
    print(f"{'✅' if dishes_found >= 3 else '❌'} Mentions multiple dishes ({dishes_found}/5): {dishes_found >= 3}")
    
    # Check for proper formatting
    lines = response2.split('\n')
    allergen_lines = [line for line in lines if line.strip() and ('מכילה' in line or 'עקבות' in line)]
    print(f"{'✅' if len(allergen_lines) >= 3 else '❌'} Multiple allergen entries found: {len(allergen_lines)}")
    
    if has_allergen_info and not has_ingredient_info and dishes_found >= 3:
        print("\n✅ TEST PASSED: Bot correctly returned allergen information")
        print("=" * 80)
        return True
    else:
        print("\n❌ TEST FAILED: Bot did not return correct allergen information")
        print("=" * 80)
        return False


async def test_ingredient_query():
    """
    Test: User asks for ingredients (to ensure we didn't break this)
    Expected: Bot returns ingredient information
    """
    print("\n" + "=" * 80)
    print("TEST: Multiple Ingredient Query (Regression Test)")
    print("=" * 80)

    service = ChatService()
    test_user = "test_ingredient_regression"

    # Step 1: Ask for עוגיות
    print("\n[User]: איזה עוגיות יש לכם?")
    response1 = await service.process_user_message(
        "איזה עוגיות יש לכם?",
        user_id=test_user,
        reset_history=True
    )
    print(f"[Bot]: {response1[:100]}...\n")

    # Step 2: Ask for ingredients
    print("[User]: מה הרכיבים של המנות שהראת לי?")
    response2 = await service.process_user_message(
        "מה הרכיבים של המנות שהראת לי?",
        user_id=test_user,
        reset_history=False
    )
    print(f"[Bot]: {response2}\n")

    print("=" * 80)
    print("VALIDATION:")
    print("=" * 80)

    # Verify response contains ingredients
    ingredient_keywords = ["קמח", "סוכר", "תמרים", "נוטלה", "שיבולת"]
    has_ingredients = any(keyword in response2 for keyword in ingredient_keywords)
    
    # Should mention multiple dishes
    dishes_found = sum(1 for dish in ["מגולגלות תמרים", "מגולגלות נוטלה", "עוגיות גרנולה"] if dish in response2)
    
    print(f"{'✅' if has_ingredients else '❌'} Contains ingredient information: {has_ingredients}")
    print(f"{'✅' if dishes_found >= 3 else '❌'} Mentions all dishes ({dishes_found}/3): {dishes_found >= 3}")
    
    if has_ingredients and dishes_found >= 3:
        print("\n✅ TEST PASSED: Ingredients still work correctly")
        print("=" * 80)
        return True
    else:
        print("\n❌ TEST FAILED: Ingredient query broken")
        print("=" * 80)
        return False


async def main():
    """Run all allergen tests"""
    print("\n" + "=" * 80)
    print("ALLERGEN QUERY FIX - TEST SUITE")
    print("Testing allergen vs ingredient query differentiation")
    print("=" * 80 + "\n")

    # Run tests
    test1_passed = await test_allergen_query()
    test2_passed = await test_ingredient_query()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"{'✅' if test1_passed else '❌'} Allergen query: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"{'✅' if test2_passed else '❌'} Ingredient query (regression): {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
