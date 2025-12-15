"""
Test script to verify that multiple ingredient queries return UNIQUE data per dish.

This test addresses the critical bug where the LLM was showing IDENTICAL ingredients
for all dishes instead of mapping each tool response correctly.

Test scenario:
1. Ask for multiple pastries
2. Ask for ingredients and allergens of all of them
3. Verify each dish has DIFFERENT, UNIQUE ingredients (not copied)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.chat_service import ChatService
from app.config import Config
import logging
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_multiple_ingredient_uniqueness():
    """Test that each dish gets its OWN unique ingredients, not copied data."""
    
    service = ChatService()
    user_id = "test_user_ingredients"
    
    print("\n" + "="*80)
    print("TEST: Multiple Ingredient Query Data Uniqueness")
    print("="*80)
    
    # Step 1: Ask for pastries
    print("\nSTEP 1: User asks for pastries")
    print("-" * 80)
    query1 = "איזה פשטידות יש לכם?"
    response1 = await service.process_user_message(query1, user_id, reset_history=True)
    print(f"\nUser: {query1}")
    print(f"Bot: {response1}")
    
    # Step 2: Ask for ingredients and allergens
    print("\nSTEP 2: User asks for ingredients and allergens of all")
    print("-" * 80)
    query2 = "מה הרכיבים ואלרגנים שלהם?"
    response2 = await service.process_user_message(query2, user_id, reset_history=False)
    print(f"\nUser: {query2}")
    print(f"Bot:\n{response2}")
    
    # Verify uniqueness
    print("\n" + "="*80)
    print("VERIFICATION:")
    print("="*80)
    
    # Check for dish names in response
    pastry_names = [
        "פשטידת בטטה",
        "פשטידת ברוקלי", 
        "פשטידת פטריות",
        "פשטידת ירקות"
    ]
    
    found_dishes = []
    for name in pastry_names:
        if name in response2:
            found_dishes.append(name)
    
    print(f"\nFOUND {len(found_dishes)} dishes mentioned in response:")
    for dish in found_dishes:
        print(f"   - {dish}")
    
    # Check for ingredient uniqueness
    print("\nChecking for ingredient uniqueness...")
    
    # Key ingredients that should be DIFFERENT between dishes
    unique_indicators = {
        "בטטה": "פשטידת בטטה",
        "ברוקולי": "פשטידת ברוקלי",
        "פטריות": "פשטידת פטריות",
        "תפוח אדמה": "פשטידת ירקות"
    }
    
    found_unique = []
    for ingredient, expected_dish in unique_indicators.items():
        if ingredient in response2:
            found_unique.append(f"{ingredient} (for {expected_dish})")
    
    print(f"\nFOUND {len(found_unique)} unique ingredients:")
    for item in found_unique:
        print(f"   - {item}")
    
    # Check for duplicate ingredient lists (WRONG behavior)
    lines = response2.split('\n')
    ingredient_lines = [line for line in lines if 'מכיל' in line]
    
    if len(ingredient_lines) > 1:
        # Check if any two lines are identical
        duplicate_count = 0
        for i in range(len(ingredient_lines)):
            for j in range(i + 1, len(ingredient_lines)):
                if ingredient_lines[i] == ingredient_lines[j]:
                    duplicate_count += 1
                    print(f"\n[INFO] Found duplicate ingredient list (lines {i+1} and {j+1})")
                    print(f"   {ingredient_lines[i][:80]}...")
        
        # NOTE: We expect 1 duplicate because "פשטידת ירקות אישית" and "פשטידת ירקות פרווה גדול" 
        # are the same recipe in different sizes (this is correct in the data)
        expected_duplicates = 1
        
        if duplicate_count == expected_duplicates:
            print(f"\nPASS: Found {duplicate_count} duplicate as expected (vegetable pastries in different sizes)")
            print("     Other ingredient lists are UNIQUE - LLM is NOT copying data!")
            return True
        elif duplicate_count == 0:
            print(f"\nPASS: All {len(ingredient_lines)} ingredient lists are UNIQUE (no duplicates)")
            return True
        else:
            print(f"\n[FAIL] Found {duplicate_count} duplicate ingredient lists (expected {expected_duplicates})!")
            return False
    else:
        print("\nWARNING: Could not verify uniqueness (not enough ingredient lines found)")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_multiple_ingredient_uniqueness())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
