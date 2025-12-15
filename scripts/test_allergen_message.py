"""
Quick test for allergen safety message
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows console encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from app.chat_service import ChatService
import asyncio

async def test_allergen_query():
    """Test allergen query with safety message"""
    print("\n" + "="*60)
    print("  Testing Allergen Safety Message")
    print("="*60 + "\n")

    chat_service = ChatService()
    test_user_id = "test_allergen_user"

    # Test queries that should trigger safety message
    queries = [
        "יש לי אלרגיה לאגוזים, מה בטוח בשבילי?",
        "אני רגיש לגלוטן, יש משהו שאני יכול לאכול?",
        "מה מתאים למי שאלרגי לחלב?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/3: {query}")
        print('='*60)

        response = await chat_service.process_user_message(query, test_user_id)
        print(f"\nBot Response:\n{response}\n")

        # Check if safety message is included
        if "במטבח משותף" in response or "ליצור קשר ישירות" in response:
            print("✅ Safety message included")
        else:
            print("⚠️  Safety message NOT found")

        print()

if __name__ == "__main__":
    asyncio.run(test_allergen_query())
