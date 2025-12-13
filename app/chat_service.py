"""
Chat Service Module - Router Pattern Implementation
Implements 3-step pipeline: Router -> Rewriter -> Main Flow
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

load_dotenv()


class ChatService:
    """
    Router-pattern chat service for SaladBot
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.session_manager = SessionManager()

    async def classify_intent(
        self,
        user_input: str,
        history: List[Dict[str, str]]
    ) -> Literal["SEARCH", "CHAT"]:
        """
        Router: Classify if user needs database search or general chat

        Args:
            user_input: User's message
            history: Conversation history

        Returns:
            "SEARCH" or "CHAT"
        """
        system_prompt = """You are a Traffic Controller. Analyze the user's message.
- **Output `SEARCH` if:**
  1. The user mentions food, ingredients, prices, availability, or categories.
  2. The input is ambiguous, slang, or vague (e.g., 'I want that thing').
  3. The input is a mix of greeting + food (e.g., 'Hi, do you have hummus?').
  4. You are in doubt. **BIAS TOWARDS SEARCH.**
- **Output `CHAT` if (and ONLY if):**
  1. The input is EXCLUSIVELY a greeting, farewell, 'thank you', or a complaint.
  2. The input is a question about store hours or location (which you know from context).
- **Output Format:** Return ONLY the single word: `SEARCH` or `CHAT`."""

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
        return "SEARCH" if result == "SEARCH" else "CHAT"

    async def rewrite_user_query(
        self,
        user_input: str,
        history: List[Dict[str, str]]
    ) -> str:
        """
        Rewriter: Convert user message into standalone Hebrew search query

        Args:
            user_input: User's original message
            history: Conversation history

        Returns:
            Rewritten standalone query
        """
        system_prompt = """Rewrite the user's last message into a clear, standalone Hebrew question based on the chat history.
- Resolve pronouns (e.g., replace 'it' with the item name from previous turns).
- Keep all filters (vegan, price, etc.).
- If the user changes the topic, ignore the old history.
- Output ONLY the rewritten sentence."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-6:] if len(history) > 6 else history)
        messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            max_tokens=150
        )

        rewritten = response.choices[0].message.content.strip()
        print(f"[Rewriter]: {user_input} -> {rewritten}")
        return rewritten

    async def process_user_message(
        self,
        user_message: str,
        user_id: str = "default_user",
        reset_history: bool = False
    ) -> str:
        """
        Main flow: Router -> Rewriter -> Database/LLM

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
            if intent == "CHAT":
                # General conversation - no database, no rewriter
                system_msg = "You are a helpful assistant for a Deli. Answer politely. Do not make up menu items."
                messages = [{"role": "system", "content": system_msg}]
                messages.extend(history[-8:] if len(history) > 8 else history)
                messages.append({"role": "user", "content": user_message})

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )

                final_content = response.choices[0].message.content

            else:  # intent == "SEARCH"
                # Step 3: Rewriter
                rewritten_query = await self.rewrite_user_query(user_message, history)

                # Prepare message with instructions
                prepared_message = prepare_user_message_with_instructions(rewritten_query)

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
