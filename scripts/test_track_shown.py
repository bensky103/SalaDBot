"""
Test script for track_shown parameter functionality
Verifies that ingredient queries don't add dishes to shown list
"""

import asyncio
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat_service import ChatService

async def test_track_shown():
    """Test that track_shown parameter works correctly"""

    chat_service = ChatService()
    # Use the session manager from chat_service (same instance)
    session_manager = chat_service.session_manager
    test_user_id = "test_track_shown_user"

    # Clear session before test
    session_manager.clear_session(test_user_id)

    print("=== Test: Track Shown Parameter ===\n")

    # Test 1: Browse chicken dishes (should track)
    print("Test 1: Browse chicken dishes (should track shown dishes)")
    print("-" * 60)
    response1 = await chat_service.process_user_message(
        "מה יש לכם בעוף?",
        user_id=test_user_id
    )
    print(f"User: מה יש לכם בעוף?")
    print(f"Bot: {response1}\n")

    shown_dishes_after_browse = session_manager.get_shown_dishes(test_user_id)
    print(f"✓ Shown dishes count after browsing: {len(shown_dishes_after_browse)}")
    print(f"  Dish IDs: {list(shown_dishes_after_browse)}\n")

    # Test 2: Ask for ingredients of specific dish (should NOT track)
    print("Test 2: Ask for ingredients (should NOT add to shown dishes)")
    print("-" * 60)
    response2 = await chat_service.process_user_message(
        "מה הרכיבים של קציצות עוף?",
        user_id=test_user_id
    )
    print(f"User: מה הרכיבים של קציצות עוף?")
    print(f"Bot: {response2}\n")

    shown_dishes_after_ingredient = session_manager.get_shown_dishes(test_user_id)
    print(f"✓ Shown dishes count after ingredient query: {len(shown_dishes_after_ingredient)}")

    if len(shown_dishes_after_ingredient) == len(shown_dishes_after_browse):
        print("✅ PASS: Ingredient query did NOT add new dishes to shown list")
    else:
        print("❌ FAIL: Ingredient query added dishes to shown list")
        print(f"  Expected: {len(shown_dishes_after_browse)}, Got: {len(shown_dishes_after_ingredient)}")

    print()

    # Test 3: Ask for ingredients again (should work without "already shown" message)
    print("Test 3: Ask for ingredients again (should return same dish)")
    print("-" * 60)
    response3 = await chat_service.process_user_message(
        "מה הרכיבים?",
        user_id=test_user_id
    )
    print(f"User: מה הרכיבים?")
    print(f"Bot: {response3}\n")

    # Check that response doesn't contain "already shown" messages
    if "כבר הוצגו" not in response3 and "זה כל המנות" not in response3:
        print("✅ PASS: Can query same dish details multiple times")
    else:
        print("❌ FAIL: Got 'already shown' message for detail query")

    print()

    # Test 4: Browse more dishes (should track and exclude previous)
    print("Test 4: Browse more dishes (should track and exclude previous)")
    print("-" * 60)
    response4 = await chat_service.process_user_message(
        "יש עוד מנות עוף?",
        user_id=test_user_id
    )
    print(f"User: יש עוד מנות עוף?")
    print(f"Bot: {response4}\n")

    shown_dishes_after_more = session_manager.get_shown_dishes(test_user_id)
    print(f"✓ Shown dishes count after 'show more': {len(shown_dishes_after_more)}")

    if len(shown_dishes_after_more) > len(shown_dishes_after_browse):
        print("✅ PASS: Browsing added new dishes to shown list")
    else:
        print("⚠️  WARNING: No new dishes added (might be all dishes shown or LLM issue)")

    print()

    # Test 5: Ask for price of specific dish (should NOT track)
    print("Test 5: Ask for price of specific dish (should NOT track)")
    print("-" * 60)
    response5 = await chat_service.process_user_message(
        "מה המחיר של חזה עוף?",
        user_id=test_user_id
    )
    print(f"User: מה המחיר של חזה עוף?")
    print(f"Bot: {response5}\n")

    shown_dishes_after_price = session_manager.get_shown_dishes(test_user_id)
    print(f"✓ Shown dishes count after price query: {len(shown_dishes_after_price)}")

    if len(shown_dishes_after_price) == len(shown_dishes_after_more):
        print("✅ PASS: Price query did NOT add new dishes to shown list")
    else:
        print("❌ FAIL: Price query added dishes to shown list")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

    # Cleanup
    session_manager.clear_session(test_user_id)

if __name__ == "__main__":
    asyncio.run(test_track_shown())
