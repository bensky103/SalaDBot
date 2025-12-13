"""
Test script to verify instructions loading and message preparation
"""

import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ai_core import SYSTEM_INSTRUCTIONS, prepare_user_message_with_instructions

def test_instructions_loading():
    """Test that instructions are loaded from file"""
    print("="*60)
    print("TEST 1: Instructions Loading")
    print("="*60)

    if SYSTEM_INSTRUCTIONS:
        print("✓ Instructions loaded successfully")
        print(f"\nInstructions length: {len(SYSTEM_INSTRUCTIONS)} characters")
        print(f"\nFirst 200 characters:")
        print(SYSTEM_INSTRUCTIONS[:200])
        print("...")

        # Check for critical content
        critical_terms = [
            "ל-100 גרם",
            "ליחידה",
            "allergens_contains",
            "allergens_traces",
            "CRITICAL"
        ]

        print("\n" + "="*60)
        print("Checking for critical business rules:")
        for term in critical_terms:
            if term in SYSTEM_INSTRUCTIONS:
                print(f"  ✓ Found: {term}")
            else:
                print(f"  ✗ Missing: {term}")
    else:
        print("✗ Instructions NOT loaded - file may be missing!")

def test_message_preparation():
    """Test message preparation with instructions appended"""
    print("\n" + "="*60)
    print("TEST 2: Message Preparation")
    print("="*60)

    user_message = "מה המחיר של סלט חומוס?"
    prepared_message = prepare_user_message_with_instructions(user_message)

    print(f"\nOriginal message: {user_message}")
    print(f"Original length: {len(user_message)} characters")
    print(f"\nPrepared message length: {len(prepared_message)} characters")

    if len(prepared_message) > len(user_message):
        print("✓ Instructions were appended to message")
    else:
        print("✗ Instructions were NOT appended!")

    # Check structure
    if "[SYSTEM INSTRUCTIONS - CRITICAL BUSINESS RULES]" in prepared_message:
        print("✓ Instructions header found in prepared message")
    else:
        print("✗ Instructions header NOT found!")

    print(f"\nPrepared message preview (first 300 chars):")
    print(prepared_message[:300])
    print("...")
    print(f"\nLast 200 chars:")
    print(prepared_message[-200:])

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  INSTRUCTIONS LOADING TEST SUITE")
    print("="*60)

    try:
        test_instructions_loading()
        test_message_preparation()

        print("\n" + "="*60)
        print("  ALL TESTS COMPLETED ✓")
        print("="*60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
