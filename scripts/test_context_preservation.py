"""
Test script to verify category context preservation across follow-up messages.

This script tests the session-based category tracking feature that solves
the problem where follow-up queries lose category context.

Example scenario that should now work correctly:
User: "איזה קינוחים יש?" (what desserts?)
Bot: Shows desserts, system saves category "קינוחים"
User: "יש לכם משהו חלבי?" (do you have something dairy?)
Bot: Should search DAIRY DESSERTS (not all dairy items)
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.session_manager import SessionManager


def test_category_tracking():
    """Test basic category tracking functionality."""
    print("\n=== Test 1: Basic Category Tracking ===")
    
    session_manager = SessionManager()
    user_id = "test_user_1"
    
    # Test setting category
    session_manager.set_last_category(user_id, "קינוחים")
    retrieved = session_manager.get_last_category(user_id)
    
    assert retrieved == "קינוחים", f"Expected 'קינוחים', got '{retrieved}'"
    print("✅ Category saved and retrieved correctly")
    
    # Test clearing category
    session_manager.clear_last_category(user_id)
    retrieved = session_manager.get_last_category(user_id)
    
    assert retrieved is None, f"Expected None after clear, got '{retrieved}'"
    print("✅ Category cleared successfully")


def test_category_timeout():
    """Test that category context expires after timeout."""
    print("\n=== Test 2: Category Timeout ===")
    
    session_manager = SessionManager()
    user_id = "test_user_2"
    
    # Set category with custom timestamp (11 minutes ago) using private accessor
    session = session_manager._get_or_create_session(user_id)
    session["last_category"] = "סלטים"
    session["last_category_time"] = datetime.now() - timedelta(minutes=11)
    
    # Should return None due to timeout (default 10 minutes)
    retrieved = session_manager.get_last_category(user_id, timeout_minutes=10)
    
    assert retrieved is None, f"Expected None after timeout, got '{retrieved}'"
    print("✅ Category correctly expired after timeout")
    
    # Set fresh category
    session_manager.set_last_category(user_id, "מנות ראשונות")
    retrieved = session_manager.get_last_category(user_id, timeout_minutes=10)
    
    assert retrieved == "מנות ראשונות", f"Expected 'מנות ראשונות', got '{retrieved}'"
    print("✅ Fresh category retrieved within timeout")


def test_multiple_users():
    """Test that categories are isolated per user."""
    print("\n=== Test 3: Multi-User Isolation ===")
    
    session_manager = SessionManager()
    user_1 = "test_user_3a"
    user_2 = "test_user_3b"
    
    # Set different categories for different users
    session_manager.set_last_category(user_1, "קינוחים")
    session_manager.set_last_category(user_2, "משקאות")
    
    retrieved_1 = session_manager.get_last_category(user_1)
    retrieved_2 = session_manager.get_last_category(user_2)
    
    assert retrieved_1 == "קינוחים", f"User 1: Expected 'קינוחים', got '{retrieved_1}'"
    assert retrieved_2 == "משקאות", f"User 2: Expected 'משקאות', got '{retrieved_2}'"
    print("✅ Categories correctly isolated per user")


def test_category_override():
    """Test that new category overrides old one."""
    print("\n=== Test 4: Category Override ===")
    
    session_manager = SessionManager()
    user_id = "test_user_4"
    
    # Set initial category
    session_manager.set_last_category(user_id, "סלטים")
    retrieved = session_manager.get_last_category(user_id)
    assert retrieved == "סלטים", f"Expected 'סלטים', got '{retrieved}'"
    
    # Override with new category
    session_manager.set_last_category(user_id, "קינוחים")
    retrieved = session_manager.get_last_category(user_id)
    assert retrieved == "קינוחים", f"Expected 'קינוחים', got '{retrieved}'"
    
    print("✅ Category correctly overridden")


def test_session_info_includes_category():
    """Test that get_session_info includes category context."""
    print("\n=== Test 5: Session Info Includes Category ===")
    
    session_manager = SessionManager()
    user_id = "test_user_5"
    
    # Set category
    session_manager.set_last_category(user_id, "מנות עיקריות")
    
    # Get session info
    info = session_manager.get_session_info(user_id)
    
    assert "last_category" in info, "Session info missing 'last_category' field"
    assert info["last_category"] == "מנות עיקריות", f"Expected 'מנות עיקריות', got '{info['last_category']}'"
    
    print("✅ Session info includes category context")


def test_dessert_dairy_scenario():
    """
    Test the actual user scenario that prompted this feature:
    User asks for desserts, then asks for dairy items without mentioning desserts again.
    Expected: Bot should search for dairy DESSERTS, not all dairy items.
    """
    print("\n=== Test 6: Dessert→Dairy Follow-up Scenario ===")
    
    session_manager = SessionManager()
    user_id = "test_user_6"
    
    # Simulate: User asks "איזה קינוחים יש?"
    # Chat service would call: get_menu_items(category="קינוחים")
    # And then save the category:
    session_manager.set_last_category(user_id, "קינוחים")
    print("Step 1: User queries desserts → Category 'קינוחים' saved")
    
    # Simulate: User asks "יש לכם משהו חלבי?"
    # Chat service would check for last_category before calling LLM:
    last_category = session_manager.get_last_category(user_id)
    
    assert last_category == "קינוחים", f"Expected 'קינוחים', got '{last_category}'"
    print(f"Step 2: Follow-up query → Retrieved category: '{last_category}'")
    print("✅ Bot would now search for dairy items within 'קינוחים' category only")


def test_greeting_clears_context():
    """
    Test that greeting/farewell clears category context.
    When user says "היי" or "תודה", previous browsing context should reset.
    """
    print("\n=== Test 7: Greeting Clears Context ===")
    
    session_manager = SessionManager()
    user_id = "test_user_7"
    
    # User was browsing salads
    session_manager.set_last_category(user_id, "סלטים")
    retrieved = session_manager.get_last_category(user_id)
    assert retrieved == "סלטים", f"Expected 'סלטים', got '{retrieved}'"
    print("Setup: User browsing 'סלטים'")
    
    # User greets (simulating get_business_info call)
    session_manager.clear_last_category(user_id)
    retrieved = session_manager.get_last_category(user_id)
    
    assert retrieved is None, f"Expected None after greeting, got '{retrieved}'"
    print("✅ Category cleared after greeting")


def test_category_list_clears_context():
    """
    Test that asking for general category list clears specific category context.
    When user asks "מה יש לכם?" after browsing specific category, context resets.
    """
    print("\n=== Test 8: Category List Clears Context ===")
    
    session_manager = SessionManager()
    user_id = "test_user_8"
    
    # User was browsing desserts
    session_manager.set_last_category(user_id, "קינוחים")
    retrieved = session_manager.get_last_category(user_id)
    assert retrieved == "קינוחים", f"Expected 'קינוחים', got '{retrieved}'"
    print("Setup: User browsing 'קינוחים'")
    
    # User asks for category list (simulating get_category_list call)
    session_manager.clear_last_category(user_id)
    retrieved = session_manager.get_last_category(user_id)
    
    assert retrieved is None, f"Expected None after category list, got '{retrieved}'"
    print("✅ Category cleared after requesting category list")


def run_all_tests():
    """Run all context preservation tests."""
    print("=" * 70)
    print("CATEGORY CONTEXT PRESERVATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_category_tracking,
        test_category_timeout,
        test_multiple_users,
        test_category_override,
        test_session_info_includes_category,
        test_dessert_dairy_scenario,
        test_greeting_clears_context,
        test_category_list_clears_context,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed} total")
    print("=" * 70)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED! Category context preservation is working correctly.")


if __name__ == "__main__":
    run_all_tests()
