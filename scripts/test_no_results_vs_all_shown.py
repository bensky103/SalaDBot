"""
Test script to verify NO_RESULTS vs ALL_DISHES_SHOWN differentiation.

This test verifies that the bot can distinguish between:
1. [ALL_DISHES_SHOWN] - All dishes in category were already browsed
2. [NO_RESULTS] - Query returned 0 results (legitimately empty)

Test scenario:
1. Browse cookies (3 dishes shown and tracked)
2. Ask about soup ingredients (detail query, NOT tracked)
3. Ask for Sunday soups (should return NO_RESULTS, not ALL_DISHES_SHOWN)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chat_service import ChatService
from app.config import Config
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_no_results_vs_all_shown():
    """Test that NO_RESULTS is returned instead of ALL_DISHES_SHOWN for empty queries."""
    
    import asyncio
    
    service = ChatService()
    user_id = "test_user_no_results"
    
    print("\n" + "="*80)
    print("TEST: NO_RESULTS vs ALL_DISHES_SHOWN Differentiation")
    print("="*80)
    
    # Step 1: Browse cookies
    print("\n📋 STEP 1: User browses cookies")
    print("-" * 80)
    query1 = "איזה עוגיות יש לכם?"
    response1 = asyncio.run(service.process_user_message(query1, user_id))
    print(f"\n👤 User: {query1}")
    print(f"🤖 Bot: {response1}")
    
    # Step 2: Ask about soup ingredients (detail query)
    print("\n📋 STEP 2: User asks about soup ingredients (detail query)")
    print("-" * 80)
    query2 = "מה הרכיבים של מרק ירקות וגריסים?"
    response2 = asyncio.run(service.process_user_message(query2, user_id))
    print(f"\n👤 User: {query2}")
    print(f"🤖 Bot: {response2}")
    
    # Step 3: Ask for Sunday soups (should be NO_RESULTS)
    print("\n📋 STEP 3: User asks for Sunday soups (expecting NO_RESULTS)")
    print("-" * 80)
    query3 = "איזה מרקים זמינים ביום ראשון?"
    response3 = asyncio.run(service.process_user_message(query3, user_id))
    print(f"\n👤 User: {query3}")
    print(f"🤖 Bot: {response3}")
    
    # Verify response
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    if "אין לנו מרקים זמינים ביום ראשון" in response3 or "לא מצאתי מרק" in response3 or "לא נמצא" in response3:
        print("✅ PASS: Bot correctly says 'no soups on Sunday' (NO_RESULTS)")
        return True
    elif "כל המנות" in response3 and "הוצגו" in response3:
        print("❌ FAIL: Bot incorrectly says 'all dishes shown' (ALL_DISHES_SHOWN)")
        print("   Expected: NO_RESULTS (legitimately empty category)")
        print("   Got: ALL_DISHES_SHOWN (false exhaustion message)")
        return False
    else:
        print("⚠️ WARNING: Unexpected response format")
        print(f"   Response: {response3}")
        return False

if __name__ == "__main__":
    try:
        success = test_no_results_vs_all_shown()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
