"""
Chat Service Module - Router Pattern Implementation
Implements 2-step pipeline: Router -> Main Flow (with context awareness)
"""

import os
import json
from typing import Dict, List, Optional, Any, Literal
from openai import OpenAI
from dotenv import load_dotenv

from app.ai_core import (
    GET_MENU_ITEMS_TOOL,
    get_menu_items_implementation,
    format_menu_items_for_ai,
    prepare_user_message_with_instructions
)
from app.session_manager import SessionManager
from app.utils import get_category_list_message

load_dotenv()


class ChatService:
    """
    Router-pattern chat service for SaladBot
    Uses 2-step pipeline: Router (intent classification) -> Main LLM (with full context preservation)
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.session_manager = SessionManager()

    async def classify_intent(
        self,
        user_input: str,
        history: List[Dict[str, str]]
    ) -> Literal["GREETING", "ORDER", "CATEGORY", "SEARCH"]:
        """
        Router: Classify user intent - greeting, order request, category list, or menu search

        Args:
            user_input: User's message
            history: Conversation history

        Returns:
            "GREETING", "ORDER", "CATEGORY", or "SEARCH" (default fallback)
        """
        # Load router instructions from file
        import os
        router_instructions_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "router_instructions.txt")
        try:
            with open(router_instructions_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            # Fallback if file not found
            system_prompt = """You are a Traffic Controller - NOT a conversational bot. Classify ONLY.
- Output `GREETING` for: Pure greetings, casual openers like "היי מה קורה", "מה נשמע", "hi", "hello", "what's up".
- Output `ORDER` for: Order/purchase/delivery inquiries.
- Output `CATEGORY` for: Category list or full menu overview requests.
- Output `SEARCH` for: Everything else (food queries, greeting+question, farewells, etc.).
Output ONLY one word: GREETING, ORDER, CATEGORY, or SEARCH."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-4:] if len(history) > 4 else history)
        messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            max_tokens=10
        )

        result = response.choices[0].message.content.strip().upper()
        print(f"[Router]: {result}")
        if result == "GREETING":
            return "GREETING"
        elif result == "ORDER":
            return "ORDER"
        elif result == "CATEGORY":
            return "CATEGORY"
        else:
            # Default to SEARCH for everything else
            return "SEARCH"

    async def process_user_message(
        self,
        user_message: str,
        user_id: str = "default_user",
        reset_history: bool = False
    ) -> str:
        """
        Main flow: Router -> Main LLM (with full context)

        Args:
            user_message: User's message text
            user_id: User identifier
            reset_history: If True, clear conversation history

        Returns:
            Bot's response in Hebrew
        """
        if reset_history:
            self.session_manager.clear_session(user_id)

        try:
            # Get conversation history
            history = self.session_manager.get_history(user_id)

            # Step 1: Router - Classify intent
            intent = await self.classify_intent(user_message, history)

            # Step 2: Branch based on intent
            if intent == "GREETING":
                # User sent a greeting - return business info
                from app.utils import get_business_info_message
                response = get_business_info_message()
                final_content = response
            elif intent == "ORDER":
                # User wants to order - redirect to website
                from app.utils import get_order_redirect_message
                response = get_order_redirect_message()
                final_content = response
            elif intent == "CATEGORY":
                # User wants category list
                response = get_category_list_message()
                final_content = response
            else:  # intent == "SEARCH"
                # Prepare message with instructions (using original message for context preservation)
                prepared_message = prepare_user_message_with_instructions(user_message)

                # Build messages for LLM
                from datetime import datetime
                import pytz
                israel_tz = pytz.timezone('Asia/Jerusalem')
                now = datetime.now(israel_tz)
                timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
                hebrew_days = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
                day_name = hebrew_days[now.weekday()]

                system_content = f"""Current Date and Time (Israel): {timestamp_str}
Today is: {day_name}

You are SaladBot, a helpful customer service assistant for Picnic Maadanim deli. You speak Hebrew only."""

                messages = [{"role": "system", "content": system_content}]
                messages.extend(history[-8:] if len(history) > 8 else history)
                messages.append({"role": "user", "content": prepared_message})

                # Call OpenAI with tool
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=[GET_MENU_ITEMS_TOOL],
                    tool_choice="auto",
                    temperature=0.7
                )

                assistant_message = response.choices[0].message

                # Check if there are tool calls
                if assistant_message.tool_calls:
                    messages.append(assistant_message)

                    for tool_call in assistant_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        if function_name == "get_menu_items":
                            exclude_ids = list(self.session_manager.get_shown_dishes(user_id))
                            print(f"[Exclusion]: Excluding {len(exclude_ids)} previously shown dishes: {exclude_ids[:10]}...")
                            
                            items = get_menu_items_implementation(
                                category=function_args.get("category"),
                                max_price=function_args.get("max_price"),
                                dietary_restriction=function_args.get("dietary_restriction"),
                                search_term=function_args.get("search_term"),
                                exclude_ids=exclude_ids if exclude_ids else None,
                                availability_day=function_args.get("availability_day")
                            )

                            if items:
                                dish_ids = [item["id"] for item in items]
                                self.session_manager.add_shown_dishes(user_id, dish_ids)
                                print(f"[Tracking]: Added {len(dish_ids)} new dishes. Total shown: {len(self.session_manager.get_shown_dishes(user_id))}")

                            function_response = format_menu_items_for_ai(items)
                        else:
                            function_response = f"Unknown tool: {function_name}"

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": function_response
                        })

                    # Get final response
                    second_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7
                    )

                    final_content = second_response.choices[0].message.content
                else:
                    final_content = assistant_message.content

            # Add to session history
            self.session_manager.add_message(user_id, "user", user_message)
            self.session_manager.add_message(user_id, "assistant", final_content)

            return final_content

        except Exception as e:
            error_msg = f"מצטערים, אירעה שגיאה. אנא נסה שוב. (Error: {str(e)})"
            print(f"Chat service error: {e}")
            return error_msg
