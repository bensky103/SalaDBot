"""
Test script for conversation context awareness
Tests that the bot maintains filters across multiple messages
"""

import sys
import os

# Fix Windows console encoding for Hebrew
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent import SaladBotAgent

def test_vegan_context():
    """Test that vegan filter is maintained in follow-up questions"""
    print("=" * 60)
    print("TEST: Vegan Context Awareness")
    print("=" * 60)

    agent = SaladBotAgent()
    test_user = "test_vegan_context"

    # First message: Ask for vegan dishes
    print("\n[User]: איזה מנות טבעוניות יש לכם?")
    response1 = agent.process_message(
        "איזה מנות טבעוניות יש לכם?",
        user_id=test_user,
        reset_history=False
    )
    print(f"[Bot]: {response1}\n")

    # Second message: Ask for desserts (should maintain vegan filter)
    print("[User]: אוקי ואיזה קינוחים?")
    response2 = agent.process_message(
        "אוקי ואיזה קינוחים?",
        user_id=test_user,
        reset_history=False
    )
    print(f"[Bot]: {response2}\n")

    # Check if the response mentions vegan or shows context awareness
    if "טבעוני" in response2.lower() or "🌱" in response2:
        print("✅ PASS: Bot maintained vegan context")
    else:
        print("⚠️  WARNING: Bot may not have maintained vegan context")
        print("   (Check if response shows only vegan desserts)")

    print("\n" + "=" * 60)

def test_category_context():
    """Test that category filter is maintained"""
    print("\n" + "=" * 60)
    print("TEST: Category Context Awareness")
    print("=" * 60)

    agent = SaladBotAgent()
    test_user = "test_category_context"

    # First message: Ask for chicken dishes
    print("\n[User]: מה יש לכם עם עוף?")
    response1 = agent.process_message(
        "מה יש לכם עם עוף?",
        user_id=test_user,
        reset_history=False
    )
    print(f"[Bot]: {response1}\n")

    # Second message: Ask about availability (should maintain chicken category)
    print("[User]: איזה מהם זמין בשישי?")
    response2 = agent.process_message(
        "איזה מהם זמין בשישי?",
        user_id=test_user,
        reset_history=False
    )
    print(f"[Bot]: {response2}\n")

    print("✅ Manual check needed: Verify response shows only chicken dishes available on Friday")
    print("=" * 60)

if __name__ == "__main__":
    print("\n🧪 CONTEXT AWARENESS TEST SUITE\n")

    try:
        test_vegan_context()
        test_category_context()

        print("\n✅ All tests completed!")
        print("\nNOTE: These tests require manual verification of the responses.")
        print("Check that follow-up questions maintain the context from previous messages.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
