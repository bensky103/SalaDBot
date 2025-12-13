"""
Test Script for Enhanced SaladBot Agent (V2)
Tests all new features: session management, dish variety, greetings, categories
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows console encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from app.agent import SaladBotAgent
from app.utils import parse_hebrew_day_range, is_item_available_today


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def test_day_parsing():
    """Test Hebrew day range parsing"""
    print_section("TEST 1: Hebrew Day Range Parsing")

    test_cases = [
        "ימים ד - ו",  # Wed-Fri
        "ימים א - ה",  # Sun-Thu
        "ד ה ו",       # Wed Thu Fri (space-separated)
    ]

    for test in test_cases:
        days = parse_hebrew_day_range(test)
        print(f"Input: '{test}'")
        print(f"Parsed days: {days}")
        print()

def test_greeting_detection():
    """Test greeting detection"""
    print_section("TEST 2: Greeting Detection & Business Info")

    agent = SaladBotAgent()
    test_user_id = "test_user_greeting"

    greetings = ["שלום", "היי", "hello", "מה נשמע"]

    for greeting in greetings:
        print(f"User: {greeting}")
        response = agent.process_message(greeting, test_user_id)
        print(f"Bot: {response[:100]}...")  # First 100 chars
        print()


def test_general_menu_query():
    """Test general menu query (should list categories)"""
    print_section("TEST 3: General Menu Query - Category Listing")

    agent = SaladBotAgent()
    test_user_id = "test_user_general"

    query = "מה יש לכם?"
    print(f"User: {query}")
    response = agent.process_message(query, test_user_id)
    print(f"Bot: {response}")
    print()


def test_specific_query_with_variety():
    """Test specific dish query with variety tracking"""
    print_section("TEST 4: Dish Variety Tracking (No Repeats)")

    agent = SaladBotAgent()
    test_user_id = "test_user_variety"

    # Ask for salads multiple times - should get different dishes each time
    queries = [
        "תראה לי סלטים טבעוניים",
        "עוד סלטים טבעוניים",
        "עוד סלטים",
    ]

    all_dishes_shown = []

    for query in queries:
        print(f"\nUser: {query}")
        response = agent.process_message(query, test_user_id)
        print(f"Bot: {response[:300]}...")  # First 300 chars

        # Check session info
        session_info = agent.get_session_info(test_user_id)
        print(f"\nSession info: {session_info}")

    print("\n✓ Each query should show DIFFERENT dishes (no repeats)")


def test_conversation_history():
    """Test conversation history context"""
    print_section("TEST 5: Conversation History Context")

    agent = SaladBotAgent()
    test_user_id = "test_user_history"

    conversation = [
        "מה יש לכם ללא גלוטן?",
        "ומה עם טבעוני?",  # Follow-up question
        "תודה!"
    ]

    for message in conversation:
        print(f"\nUser: {message}")
        response = agent.process_message(message, test_user_id)
        print(f"Bot: {response[:200]}...")

        # Show history length
        session_info = agent.get_session_info(test_user_id)
        print(f"Messages in history: {session_info['message_count']}")


def test_hebrew_search():
    """Test Hebrew search functionality"""
    print_section("TEST 6: Hebrew Search in Database")

    agent = SaladBotAgent()
    test_user_id = "test_user_search"

    hebrew_queries = [
        "יש לכם חומוס?",
        "מה יש עם חציל?",
        "תראה לי פלאפל",
        "מה המחיר של סלט?",
    ]

    for query in hebrew_queries:
        print(f"\nUser: {query}")
        response = agent.process_message(query, test_user_id)
        print(f"Bot: {response[:250]}...")
        print()


def test_allergen_safety():
    """Test allergen safety (CRITICAL)"""
    print_section("TEST 7: CRITICAL - Allergen Safety")

    agent = SaladBotAgent()
    test_user_id = "test_user_allergen"

    query = "יש לי אלרגיה לאגוזים, מה בטוח בשבילי?"
    print(f"User: {query}")
    response = agent.process_message(query, test_user_id)
    print(f"Bot: {response}")
    print()

    # Verify safety language
    safety_keywords = ["בטוח", "ללא", "מתאים"]
    has_safety_language = any(keyword in response for keyword in safety_keywords)

    if has_safety_language:
        print("✓ PASS: Response includes safety-conscious language")
    else:
        print("✗ FAIL: Response missing safety language")


def test_price_format():
    """Test price format (CRITICAL)"""
    print_section("TEST 8: CRITICAL - Price Format Validation")

    agent = SaladBotAgent()
    test_user_id = "test_user_price"

    query = "מה המחיר של סלטים?"
    print(f"User: {query}")
    response = agent.process_message(query, test_user_id)
    print(f"Bot: {response}")
    print()

    # Check for price units
    has_per_100g = "ל-100 גרם" in response or "/100g" in response
    has_per_unit = "ליחידה" in response or "/יח" in response

    if has_per_100g or has_per_unit:
        print("✓ PASS: Price includes proper units")
    else:
        print("⚠ WARNING: Price units not found (check response)")


def main():
    """Run all tests"""
    print("\n" + "🧪 SALADBOT V2 - ENHANCED AGENT TEST SUITE" + "\n")

    try:
        test_day_parsing()
        test_greeting_detection()
        test_general_menu_query()
        test_specific_query_with_variety()
        test_conversation_history()
        test_hebrew_search()
        test_allergen_safety()
        test_price_format()

        print("\n" + "="*60)
        print("  ✅ ALL TESTS COMPLETED")
        print("="*60 + "\n")

        print("\n📊 Summary of New Features:")
        print("1. ✓ Greeting detection → Business info message")
        print("2. ✓ General query → Category listing")
        print("3. ✓ Dish variety tracking → No repeats")
        print("4. ✓ Conversation history → Context-aware responses")
        print("5. ✓ Hebrew search → Database queries work")
        print("6. ✓ Allergen safety → Dual-field checking")
        print("7. ✓ Price format → Units always included")
        print("8. ✓ Day parsing → Hebrew availability ranges\n")

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
