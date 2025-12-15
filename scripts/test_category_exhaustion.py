"""
Test script for category exhaustion bug fix
Verifies that bot doesn't return wrong category dishes when all items shown
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


async def test_cookies_category_exhaustion():
    """
    Test: User asks for עוגיות, then "מה עוד?" after all shown
    Bug: Bot was returning קינוחים dishes instead of "all shown" message
    Expected: Bot should say "זה כל המנות בקטגוריה זו" (that's all the dishes)
    """
    print("=" * 80)
    print("TEST: עוגיות Category Exhaustion (Bug Fix)")
    print("=" * 80)

    service = ChatService()
    test_user = "test_cookies_exhaustion"

    # First request - show עוגיות
    print("\n[Request #1]: איזה עוגיות יש לכם?")
    response1 = await service.process_user_message(
        "איזה עוגיות יש לכם?",
        user_id=test_user,
        reset_history=True
    )
    print(f"[Bot]: {response1}\n")
    
    # Verify we got cookies (should contain מגולגלות or עוגיות in response)
    has_cookies = "מגולגלות" in response1 or "עוגיות" in response1
    print(f"{'✅' if has_cookies else '❌'} Response contains עוגיות dishes: {has_cookies}")
    
    # Get shown count
    shown_count = len(service.session_manager.get_shown_dishes(test_user))
    print(f"[Info]: Dishes shown so far: {shown_count}")

    # Second request - ask for more
    print("\n[Request #2]: מה עוד?")
    response2 = await service.process_user_message(
        "מה עוד?",
        user_id=test_user,
        reset_history=False
    )
    print(f"[Bot]: {response2}\n")

    # CRITICAL CHECK: Response should NOT contain קינוחים items
    # Common קינוחים items: מוס, טירמיסו, פנה קוטה, עוגת גבינה
    dessert_words = ["מוס דואט", "מוס שוקולד", "מוס גבינה", "עוגת גבינה", "טירמיסו", "פנה קוטה"]
    has_desserts = any(word in response2 for word in dessert_words)
    
    # Should indicate all shown
    has_all_shown_message = any(phrase in response2 for phrase in [
        "זה כל", "כבר הוצגו", "אין עוד", "ALL_DISHES_SHOWN"
    ])
    
    print("\n" + "=" * 80)
    print("RESULTS:")
    print("=" * 80)
    print(f"{'❌' if has_desserts else '✅'} Does NOT contain קינוחים dishes (מוס, etc.): {not has_desserts}")
    print(f"{'✅' if has_all_shown_message else '❌'} Contains 'all shown' message: {has_all_shown_message}")
    
    if not has_desserts and has_all_shown_message:
        print("\n✅ TEST PASSED: Category exhaustion handled correctly!")
    else:
        print("\n❌ TEST FAILED: Bug still present")
        if has_desserts:
            print("   - Bot returned קינוחים dishes instead of 'all shown' message")
        if not has_all_shown_message:
            print("   - Bot did not indicate all dishes were shown")
    
    print("=" * 80 + "\n")
    return not has_desserts and has_all_shown_message


async def test_general_category_exhaustion():
    """
    Test: General category exhaustion detection
    Expected: After all dishes shown, bot should indicate completion
    """
    print("=" * 80)
    print("TEST: General Category Exhaustion Detection")
    print("=" * 80)

    service = ChatService()
    test_user = "test_general_exhaustion"

    # Test with קרקרים category (usually has few items)
    print("\n[Test Category]: קרקרים (crackers)")
    
    # Request repeatedly until exhausted
    max_attempts = 10
    for i in range(max_attempts):
        message = "איזה קרקרים יש?" if i == 0 else "יש עוד?"
        print(f"\n[Request #{i+1}]: {message}")
        
        response = await service.process_user_message(
            message,
            user_id=test_user,
            reset_history=(i == 0)
        )
        
        # Check for completion signal
        is_complete = any(phrase in response for phrase in [
            "זה כל", "כבר הוצגו", "אין עוד"
        ])
        
        if is_complete:
            print(f"[Bot]: {response}")
            print(f"\n✅ Category exhausted after {i+1} requests")
            print(f"[Info]: Total dishes shown: {len(service.session_manager.get_shown_dishes(test_user))}")
            return True
        
        # Just show truncated response
        print(f"[Bot]: {response[:80]}...")
    
    print(f"\n⚠️ Category not exhausted after {max_attempts} requests")
    return False


async def main():
    """Run all category exhaustion tests"""
    print("\n" + "=" * 80)
    print("CATEGORY EXHAUSTION FIX - TEST SUITE")
    print("Testing fix for retry mechanism bug")
    print("=" * 80 + "\n")

    # Run tests
    test1_passed = await test_cookies_category_exhaustion()
    test2_passed = await test_general_category_exhaustion()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"{'✅' if test1_passed else '❌'} עוגיות exhaustion fix: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"{'✅' if test2_passed else '❌'} General exhaustion detection: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
