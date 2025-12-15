"""
Test script for dish repetition fix
Verifies that bot detects when all dishes have been shown
"""

import sys
import os
import asyncio

# Fix Windows console encoding for Hebrew
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chat_service import ChatService


async def test_repetition_detection():
    """
    Test: User repeatedly asks for same category dishes
    Expected: After all dishes shown, bot should say "that's all we have"
    """
    print("=" * 80)
    print("TEST: Dish Repetition Detection")
    print("=" * 80)

    service = ChatService()
    test_user = "test_repetition"

    # Ask for soups multiple times
    for i in range(5):
        print(f"\n[Request #{i+1}]: איזה מרקים יש?")
        response = await service.process_user_message(
            "איזה מרקים יש?" if i == 0 else "תראה לי עוד",
            user_id=test_user,
            reset_history=(i == 0)  # Reset only on first request
        )
        print(f"[Bot]: {response}\n")
        
        # Check if bot indicates all dishes shown
        if "[ALL_DISHES_SHOWN]" in response or "כבר הוצגו" in response or "זה כל" in response:
            print(f"✅ SUCCESS: Bot detected all dishes shown after {i+1} requests")
            break
        
        if i == 4:
            print("⚠️  WARNING: Bot didn't signal all dishes shown after 5 requests")
    
    # Show tracking info
    shown_count = len(service.session_manager.get_shown_dishes(test_user))
    print(f"\n[Info]: Total dishes tracked: {shown_count}")
    
    print("\n" + "=" * 80 + "\n")


async def test_exclusion_logging():
    """
    Test: Verify exclusion logging is working
    Expected: Console logs should show exclusion counts
    """
    print("=" * 80)
    print("TEST: Exclusion Logging Verification")
    print("=" * 80)

    service = ChatService()
    test_user = "test_logging"

    print("\n[Request #1]: איזה מרקים יש?")
    print("Expected: [Exclusion]: Excluding 0 previously shown dishes\n")
    response1 = await service.process_user_message(
        "איזה מרקים יש?",
        user_id=test_user,
        reset_history=True
    )
    print(f"[Bot]: {response1[:100]}...\n")

    print("[Request #2]: תראה לי עוד")
    print("Expected: [Exclusion]: Excluding 5 previously shown dishes\n")
    response2 = await service.process_user_message(
        "תראה לי עוד",
        user_id=test_user,
        reset_history=False
    )
    print(f"[Bot]: {response2[:100]}...\n")

    print("✅ Check console output above for [Exclusion] and [Tracking] logs")
    print("\n" + "=" * 80 + "\n")


async def main():
    """Run all repetition tests"""
    print("\n" + "=" * 80)
    print("DISH REPETITION FIX - TEST SUITE")
    print("Verifying detection of repeated content")
    print("=" * 80 + "\n")

    await test_repetition_detection()
    await test_exclusion_logging()

    print("=" * 80)
    print("TESTS COMPLETED")
    print("=" * 80)
    print("\nExpected Behavior:")
    print("  1. First request shows 5 dishes")
    print("  2. Subsequent requests show NEW dishes (not repeats)")
    print("  3. When no new dishes available, bot says 'that's all we have'")
    print("  4. Console logs show [Exclusion] and [Tracking] messages")


if __name__ == "__main__":
    asyncio.run(main())
