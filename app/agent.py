"""
OpenAI Agent Wrapper for SaladBot
Handles GPT-4o-mini integration with function calling for menu queries

Features:
- Session management with conversation history
- Dish variety tracking (no repeats)
- Greeting and general query detection
- Token-efficient context management
"""

import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv

# Import our AI core functions
from app.ai_core import (
    GET_MENU_ITEMS_TOOL,
    get_menu_items_implementation,
    format_menu_items_for_ai,
    prepare_user_message_with_instructions,
    get_category_total_count
)
from app.session_manager import SessionManager
from app.utils import (
    is_greeting_or_generic,
    is_general_menu_query,
    is_allergen_query,
    get_business_info_message,
    get_category_list_message,
    get_allergen_safety_message
)

# Load environment variables
load_dotenv()


class SaladBotAgent:
    """
    OpenAI-powered conversational agent for SaladBot
    Uses GPT-4o-mini with function calling to answer menu queries in Hebrew
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the SaladBot agent

        Args:
            model: OpenAI model to use (default: gpt-4o-mini)
        """
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.session_manager = SessionManager()

    def _get_system_message(self) -> dict:
        """
        Generate system message with current date/time context.
        Called fresh for each request to ensure accurate time.

        Returns:
            System message dict with role and content
        """
        from datetime import datetime
        import pytz

        # Get current time in Israel timezone
        israel_tz = pytz.timezone('Asia/Jerusalem')
        now = datetime.now(israel_tz)

        # Format timestamp
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")

        # Hebrew day mapping (Monday=0 in Python, but Sunday=first day in Hebrew week)
        # Python weekday: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
        # Hebrew days: Sun=ראשון, Mon=שני, Tue=שלישי, Wed=רביעי, Thu=חמישי, Fri=שישי, Sat=שבת
        hebrew_days = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
        day_name = hebrew_days[now.weekday()]

        system_content = f"""Current Date and Time (Israel): {timestamp_str}
Today is: {day_name}

You are SaladBot, a helpful customer service assistant for Picnic Maadanim deli. You speak Hebrew only."""

        return {
            "role": "system",
            "content": system_content
        }

    def _execute_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_id: str
    ) -> str:
        """
        Execute a tool/function call requested by GPT

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            user_id: User identifier for dish tracking

        Returns:
            Formatted result string for GPT
        """
        if tool_name == "get_menu_items":
            category = tool_args.get("category")
            dietary_restriction = tool_args.get("dietary_restriction")
            availability_day = tool_args.get("availability_day")

            # Get list of dishes already shown to this user
            exclude_ids = list(self.session_manager.get_shown_dishes(user_id))

            # Get or update category context
            prev_category, prev_total = self.session_manager.get_category_context(user_id)

            # If category query, get total count
            if category and category.strip():
                # If new category, get fresh count
                if category != prev_category:
                    total_count = get_category_total_count(
                        category=category,
                        dietary_restriction=dietary_restriction,
                        availability_day=availability_day
                    )
                    self.session_manager.set_category_context(user_id, category, total_count)
                else:
                    total_count = prev_total
            else:
                total_count = 0

            # Call implementation with exclusion list
            items = get_menu_items_implementation(
                category=category,
                max_price=tool_args.get("max_price"),
                dietary_restriction=dietary_restriction,
                search_term=tool_args.get("search_term"),
                exclude_ids=exclude_ids if exclude_ids else None,
                availability_day=availability_day
            )

            # Track the shown dishes (global variety tracking)
            if items:
                dish_ids = [item["id"] for item in items]
                self.session_manager.add_shown_dishes(user_id, dish_ids)

                # Also track category-specific count if category query
                if category and total_count > 0:
                    self.session_manager.add_category_shown_dishes(user_id, dish_ids)

            # Format for AI (no counter - internal tracking only)
            formatted_items = format_menu_items_for_ai(items)

            if category and total_count > 0:
                # Use category-specific shown count
                shown_count = self.session_manager.get_category_shown_count(user_id)
                # Cap shown count at total (in case of duplicates/issues)
                shown_count = min(shown_count, total_count)

                # Add counter as HIDDEN system note (not shown to user, only for AI tracking)
                counter_info = f"[INTERNAL: Shown {shown_count}/{total_count} dishes from category {category}. If user asks for more and shown=total, say 'זה כל המנות'.]\n\n"
                return counter_info + formatted_items

            return formatted_items
        else:
            return f"Unknown tool: {tool_name}"

    def process_message(
        self,
        user_message: str,
        user_id: str = "default_user",
        reset_history: bool = False
    ) -> str:
        """
        Process a user message and generate response

        Args:
            user_message: User's message text
            user_id: User identifier (WhatsApp ID or default for backward compatibility)
            reset_history: If True, clear conversation history

        Returns:
            Bot's response in Hebrew
        """
        if reset_history:
            self.session_manager.clear_session(user_id)

        try:
            # Check for greeting or generic message
            if is_greeting_or_generic(user_message):
                response = get_business_info_message()
                # Add to history
                self.session_manager.add_message(user_id, "user", user_message)
                self.session_manager.add_message(user_id, "assistant", response)
                return response

            # Check for general menu query (should list categories)
            if is_general_menu_query(user_message):
                response = get_category_list_message()
                # Add to history
                self.session_manager.add_message(user_id, "user", user_message)
                self.session_manager.add_message(user_id, "assistant", response)
                return response

            # Prepare user message with instructions
            prepared_message = prepare_user_message_with_instructions(user_message)

            # Get conversation history (last few exchanges)
            history = self.session_manager.get_history(user_id)

            # Build messages array for OpenAI (with fresh date/time)
            messages = [self._get_system_message()]

            # Add history (last N messages for context)
            messages.extend(history)

            # Add current message
            messages.append({"role": "user", "content": prepared_message})

            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[GET_MENU_ITEMS_TOOL],
                tool_choice="auto",
                temperature=0.7
            )

            # Get the assistant's response
            assistant_message = response.choices[0].message

            # Check if there are tool calls
            if assistant_message.tool_calls:
                # Add assistant's tool call message to history
                messages.append(assistant_message)

                # Track if this was an allergen query with few results
                allergen_query_with_few_results = False

                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # Check if this is an allergen-related query
                    if (function_name == "get_menu_items" and
                        is_allergen_query(user_message) and
                        function_args.get("dietary_restriction")):

                        # Execute the tool to see how many results
                        exclude_ids = list(self.session_manager.get_shown_dishes(user_id))
                        items = get_menu_items_implementation(
                            category=function_args.get("category"),
                            max_price=function_args.get("max_price"),
                            dietary_restriction=function_args.get("dietary_restriction"),
                            search_term=function_args.get("search_term"),
                            exclude_ids=exclude_ids if exclude_ids else None
                        )

                        # If very few results (0-2 items), flag for safety message
                        if len(items) <= 2:
                            allergen_query_with_few_results = True

                        # Use cached result
                        function_response = format_menu_items_for_ai(items)

                        # Track shown dishes
                        if items:
                            dish_ids = [item["id"] for item in items]
                            self.session_manager.add_shown_dishes(user_id, dish_ids)
                    else:
                        # Execute normally
                        function_response = self._execute_tool_call(
                            function_name,
                            function_args,
                            user_id
                        )

                    # Add tool response to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": function_response
                    })

                # If allergen query with few results, append safety message
                if allergen_query_with_few_results:
                    messages.append({
                        "role": "system",
                        "content": f"IMPORTANT: Very few items are safe. Append this safety message to your response:\n\n{get_allergen_safety_message()}"
                    })

                # Get final response from GPT with tool results
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )

                final_content = second_response.choices[0].message.content
            else:
                # No tool calls, use direct response
                final_content = assistant_message.content

            # Add to session history
            self.session_manager.add_message(user_id, "user", user_message)
            self.session_manager.add_message(user_id, "assistant", final_content)

            return final_content

        except Exception as e:
            error_msg = f"מצטערים, אירעה שגיאה. אנא נסה שוב. (Error: {str(e)})"
            print(f"Agent error: {e}")
            return error_msg

    def reset_shown_dishes(self, user_id: str):
        """
        Reset shown dishes for user (e.g., after they've seen many dishes)

        Args:
            user_id: User identifier
        """
        self.session_manager.reset_shown_dishes(user_id)

    def get_session_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get session information for debugging

        Args:
            user_id: User identifier

        Returns:
            Session info dictionary
        """
        return self.session_manager.get_session_info(user_id)


# Convenience function for single-message queries (stateless)
def query_saladbot(message: str, user_id: str = "default_user") -> str:
    """
    Convenience function for single-message queries

    Args:
        message: User message in Hebrew
        user_id: Optional user identifier

    Returns:
        Bot response in Hebrew
    """
    agent = SaladBotAgent()
    return agent.process_message(message, user_id=user_id, reset_history=True)


if __name__ == "__main__":
    # Quick test
    print("SaladBot Agent - Quick Test")
    print("=" * 50)

    agent = SaladBotAgent()
    test_user = "test_user"

    # Test query
    test_message = "מה יש לכם ללא גלוטן?"
    print(f"\nUser: {test_message}")

    response = agent.process_message(test_message, user_id=test_user)
    print(f"\nBot: {response}")
