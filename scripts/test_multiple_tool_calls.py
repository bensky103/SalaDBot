"""
Test Multiple Tool Calls Handling
Tests that the system can handle when OpenAI makes multiple tool calls
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat_service import ChatService
from app.config import Config

def test_multiple_tool_calls():
    """Test that multiple tool calls are handled correctly"""

    print("\n" + "="*70)
    print("  TESTING MULTIPLE TOOL CALLS HANDLING")
    print("="*70 + "\n")

    # Initialize chat service
    chat_service = ChatService()

    # Test case: User asks about ingredients of multiple items
    # This should trigger multiple get_menu_items calls
    test_query = "מה המרכיבים של סלט חומוס וסלט חציל?"

    print(f"Test Query: {test_query}")
    print(f"Expected: OpenAI may call get_menu_items multiple times")
    print(f"          System should handle ALL tool calls and respond to each\n")

    print("Running query...")

    try:
        response = chat_service.process_user_message(
            user_message=test_query,
            user_id="test_user_multiple_calls"
        )

        print("\n" + "-"*70)
        print("Response received:")
        print("-"*70)
        print(response)
        print("-"*70)

        # Check if response is an error
        if "שגיאה" in response or "מצטערים" in response:
            print("\n❌ ERROR: System returned error message")
            print("   This suggests multiple tool calls are NOT being handled correctly")
            return False
        else:
            print("\n✓ SUCCESS: System handled the query without errors")
            print("   Multiple tool calls (if any) were processed correctly")
            return True

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_multiple_tool_calls()

    print("\n" + "="*70)
    if success:
        print("  TEST PASSED ✓")
    else:
        print("  TEST FAILED ✗")
    print("="*70 + "\n")

    sys.exit(0 if success else 1)
