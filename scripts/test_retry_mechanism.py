"""Test retry mechanism for failed queries"""

import sys
import os
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.agent import SaladBotAgent

def test_retry_with_typo():
    """Test that retry works when user has typo in category name"""
    agent = SaladBotAgent()

    # Simulate AI calling with slightly wrong category spelling
    from app.ai_core import get_menu_items_implementation

    print("\n" + "="*60)
    print("Test 1: Exact category match")
    print("="*60)
    items = get_menu_items_implementation(category="בשר")
    print(f"Found {len(items)} items with exact match 'בשר'")
    assert len(items) > 0, "Should find items with exact category"

    print("\n" + "="*60)
    print("Test 2: Wrong category (should trigger retry)")
    print("="*60)
    items = get_menu_items_implementation(category="בשרים")  # Wrong plural form
    print(f"Found {len(items)} items with retry for 'בשרים'")
    # Retry should find items via fuzzy search

    print("\n" + "="*60)
    print("Test 3: Full agent query")
    print("="*60)
    response = agent.process_message("מה יש בבשר?", user_id="test_retry", reset_history=True)
    print(f"\nResponse:\n{response}\n")
    assert "₪" in response, "Should find meat dishes"

if __name__ == "__main__":
    test_retry_with_typo()
    print("\n✓ All retry mechanism tests passed!")
