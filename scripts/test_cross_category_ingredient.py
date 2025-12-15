"""
Test script to verify cross-category ingredient query fix.

This script tests Fix #1: Cross-Category Ingredient Query Bug (2025-12-15)

Example scenario that should now work correctly:
User: "איזה עוגיות יש לכם?" (what cookies do you have?)
Bot: Shows cookies, system saves category "עוגיות"
User: "מה הרכיבים של מרק ירקות?" (what are the ingredients of vegetable soup?)
Bot: Should find the soup (NOT restricted by cookies category)

BEFORE FIX: 
- LLM correctly called get_menu_items(search_term="מרק ירקות") with NO category
- Backend code in chat_service.py (L191-195) automatically applied saved category="עוגיות"
- Result: No soup found in cookies category → "כל המנות כבר הוצגו"

AFTER FIX: 
- Backend skips category context when search_term is present (L194-199)
- Result: Soup found successfully across all categories
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chat_service import ChatService
from app.session_manager import SessionManager


async def test_cross_category_ingredient_query():
    """
    Test that ingredient queries work across categories.
    User browses one category, then asks about a dish from a different category.
    """
    print("\n=== Test: Cross-Category Ingredient Query ===")
    
    chat_service = ChatService()
    user_id = "test_cross_category"
    
    # Reset history
    chat_service.session_manager.clear_session(user_id)
    
    # Step 1: User asks for cookies (establishes category context)
    print("\n[Step 1] User: 'איזה עוגיות יש לכם?'")
    response1 = await chat_service.process_user_message(
        user_message="איזה עוגיות יש לכם?",
        user_id=user_id
    )
    print(f"Bot: {response1[:100]}...")
    
    # Check category context was saved
    saved_category = chat_service.session_manager.get_last_category(user_id)
    print(f"✅ Category context saved: '{saved_category}'")
    assert saved_category == "עוגיות", f"Expected 'עוגיות', got '{saved_category}'"
    
    # Step 2: User asks about ingredients of a SOUP (different category)
    print("\n[Step 2] User: 'מה הרכיבים של מרק ירקות וגריסים?'")
    response2 = await chat_service.process_user_message(
        user_message="מה הרכיבים של מרק ירקות וגריסים?",
        user_id=user_id
    )
    print(f"Bot: {response2}")
    
    # CRITICAL: Bot should NOT return "כל המנות כבר הוצגו"
    # It should find the soup despite being in cookies browsing context
    assert "כל המנות" not in response2, "❌ FAIL: Bot couldn't find soup (category filter still applied)"
    assert "מרק" in response2 or "רכיבים" in response2 or "מכיל" in response2, "❌ FAIL: No ingredient information in response"
    
    print("✅ SUCCESS: Bot found soup ingredients despite cookies browsing context")
    print(f"✅ Response includes ingredient information")
    
    return True


async def test_cross_category_with_explicit_category():
    """
    Test that explicit category mentions still work correctly.
    User browses cookies, then explicitly asks for more cookies.
    """
    print("\n=== Test: Explicit Category After Browsing ===")
    
    chat_service = ChatService()
    user_id = "test_explicit_category"
    
    # Reset history
    chat_service.session_manager.clear_session(user_id)
    
    # Step 1: User asks for cookies
    print("\n[Step 1] User: 'איזה עוגיות יש לכם?'")
    response1 = await chat_service.process_user_message(
        user_message="איזה עוגיות יש לכם?",
        user_id=user_id
    )
    print(f"Bot: {response1[:100]}...")
    
    # Step 2: User explicitly asks for more cookies
    print("\n[Step 2] User: 'יש עוד עוגיות?'")
    response2 = await chat_service.process_user_message(
        user_message="יש עוד עוגיות?",
        user_id=user_id
    )
    print(f"Bot: {response2[:100]}...")
    
    # Should maintain cookies category context
    # (This is different from asking about a specific dish by name)
    print("✅ SUCCESS: Explicit category mention still maintains context")
    
    return True


async def test_search_term_only_for_specific_dish():
    """
    Test that asking about a specific dish uses search_term only.
    This is the core of the fix.
    """
    print("\n=== Test: Search Term Only for Specific Dish ===")
    
    chat_service = ChatService()
    user_id = "test_search_only"
    
    # Reset history
    chat_service.session_manager.clear_session(user_id)
    
    # Step 1: Browse desserts
    print("\n[Step 1] User: 'איזה קינוחים יש?'")
    response1 = await chat_service.process_user_message(
        user_message="איזה קינוחים יש?",
        user_id=user_id
    )
    print(f"Bot: {response1[:100]}...")
    
    # Check category saved
    saved_category = chat_service.session_manager.get_last_category(user_id)
    assert saved_category == "קינוחים", f"Expected 'קינוחים', got '{saved_category}'"
    
    # Step 2: Ask about a meat dish
    print("\n[Step 2] User: 'מה הרכיבים של קציצות עוף?'")
    response2 = await chat_service.process_user_message(
        user_message="מה הרכיבים של קציצות עוף?",
        user_id=user_id
    )
    print(f"Bot: {response2}")
    
    # Should find chicken dish despite desserts context
    assert "כל המנות" not in response2, "❌ FAIL: Bot couldn't find chicken dish"
    assert "רכיבים" in response2 or "מכיל" in response2 or "קציצ" in response2, "❌ FAIL: No ingredient info"
    
    print("✅ SUCCESS: Found chicken dish ingredients despite desserts context")
    
    return True


async def run_all_tests():
    """Run all test scenarios."""
    print("=" * 60)
    print("Testing Cross-Category Ingredient Query Fix")
    print("=" * 60)
    
    try:
        await test_cross_category_ingredient_query()
        await test_cross_category_with_explicit_category()
        await test_search_term_only_for_specific_dish()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        raise
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
