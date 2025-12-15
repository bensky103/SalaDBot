"""Quick test to check formatting behavior"""
import asyncio
from app.chat_service import ChatService

async def main():
    service = ChatService()

    # Test browsing query
    print("=" * 60)
    print("TEST 1: Browsing query (should show minimal info)")
    print("=" * 60)
    response = await service.process_user_message(
        user_message="איזה מרקים יש לכם?",
        user_id="test_user_123",
        reset_history=True
    )
    print(f"\nResponse:\n{response}\n")

    # Test "show more"
    print("=" * 60)
    print("TEST 2: Show more (should also be minimal)")
    print("=" * 60)
    response = await service.process_user_message(
        user_message="מה עוד?",
        user_id="test_user_123",
        reset_history=False
    )
    print(f"\nResponse:\n{response}\n")

if __name__ == "__main__":
    asyncio.run(main())
