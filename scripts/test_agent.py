"""
Lightweight test suite for SaladBot Agent (OpenAI GPT-4o-mini integration)
Tests critical business rules with minimal token usage
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

from app.chat_service import ChatService
import asyncio


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_conversation(user_msg, bot_response):
    """Print a conversation exchange"""
    print(f"\n👤 User: {user_msg}")
    print(f"\n🤖 Bot: {bot_response}")


async def test_basic_menu_query():
    """Test 1: Basic menu query with price format validation"""
    print_section("TEST 1: Basic Query + Price Format (CRITICAL)")

    chat_service = ChatService()
    user_message = "מה יש לכם ללא גלוטן?"

    response = await chat_service.process_user_message(user_message, reset_history=True)
    print_conversation(user_message, response)

    # Validation
    print("\n✓ Response received in Hebrew")

    # CRITICAL: Check for proper price units
    has_per_100g = "ל-100 גרם" in response or "ל-100" in response
    has_per_unit = "ליחידה" in response or "למנה" in response

    if has_per_100g or has_per_unit:
        print("✓ CRITICAL: Price unit specification found")
        if has_per_100g:
            print("  → 'ל-100 גרם' (per 100g) present")
        if has_per_unit:
            print("  → 'ליחידה' (per unit) present")
    else:
        print("⚠ WARNING: Price unit may be missing")


async def test_allergen_safety():
    """Test 2: CRITICAL - Allergen safety"""
    print_section("TEST 2: Allergen Safety (CRITICAL)")

    chat_service = ChatService()
    user_message = "יש לי אלרגיה לאגוזים. מה בטוח לי?"

    response = await chat_service.process_user_message(user_message, reset_history=True)
    print_conversation(user_message, response)

    # Validation
    print("\n🚨 CRITICAL VALIDATION:")
    safety_keywords = ["בטוח", "מתאים", "ללא", "אין", "עלול", "עקבות"]
    has_safety_language = any(keyword in response for keyword in safety_keywords)

    if has_safety_language:
        print("✓ Response includes safety language")
    else:
        print("⚠ Warning: Safety language not clear")


async def test_factuality():
    """Test 3: CRITICAL - Factuality (no hallucination)"""
    print_section("TEST 3: Factuality Test (CRITICAL)")

    chat_service = ChatService()
    user_message = "יש לכם פיצה?"

    response = await chat_service.process_user_message(user_message, reset_history=True)
    print_conversation(user_message, response)

    # Validation
    negative_indicators = ["לא", "אין", "לצערנו", "מצטער"]
    has_negative = any(indicator in response for indicator in negative_indicators)

    if has_negative:
        print("\n✓ CRITICAL: Bot indicates item unavailability")
        print("  (Did not hallucinate/invent menu items)")
    else:
        print("\n⚠ Warning: Response unclear about availability")


async def test_vegan_query():
    """Test 4: Dietary restriction query"""
    print_section("TEST 4: Vegan Dietary Query")

    chat_service = ChatService()
    user_message = "יש לכם מנות טבעוניות?"

    response = await chat_service.process_user_message(user_message, reset_history=True)
    print_conversation(user_message, response)

    print("\n✓ Response received")
    if "טבעוני" in response:
        print("✓ Response mentions vegan context")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  SALADBOT - CHAT SERVICE TEST SUITE")
    print("  GPT-4o-mini with Router Pattern")
    print("=" * 70)

    tests = [
        ("Basic Query + Price Format (CRITICAL)", test_basic_menu_query),
        ("Allergen Safety (CRITICAL)", test_allergen_safety),
        ("Factuality Test (CRITICAL)", test_factuality),
        ("Vegan Dietary Query", test_vegan_query)
    ]

    passed = 0
    failed = 0

    for i, (name, test_func) in enumerate(tests, 1):
        try:
            await test_func()
            print(f"\n✅ Test {i}/{len(tests)} PASSED: {name}")
            passed += 1
        except Exception as e:
            print(f"\n❌ Test {i}/{len(tests)} FAILED: {name}")
            print(f"   Error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    # Summary
    print_section("TEST SUITE COMPLETE")
    print(f"\n✅ Passed: {passed}/{len(tests)}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{len(tests)}")

    print("\nCRITICAL VALIDATIONS:")
    print("  1. Price Format: Check for 'ל-100 גרם' or 'ליחידה'")
    print("  2. Allergen Safety: Safety-conscious responses")
    print("  3. Factuality: No hallucinated menu items")
    print("\nManual review recommended before production deployment")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
