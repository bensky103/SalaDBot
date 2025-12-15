"""
Chat Service Module - Single LLM with Function Calling
Unified conversation flow with context-aware responses
"""

import json
import logging
from typing import Optional
from openai import OpenAI

from app.config import Config
from app.ai_core import (
    GET_MENU_ITEMS_TOOL,
    GET_BUSINESS_INFO_TOOL,
    GET_ORDER_INFO_TOOL,
    GET_CATEGORY_LIST_TOOL,
    get_menu_items_implementation,
    format_menu_items_for_ai,
    SYSTEM_INSTRUCTIONS
)
from app.session_manager import SessionManager
from app.utils import (
    get_business_info_message,
    get_order_redirect_message,
    get_category_list_message
)


logger = logging.getLogger(Config.LOGGER_NAME)


class ChatService:
    """
    Single LLM chat service for SaladBot
    Uses unified flow with function calling and context-aware responses
    """

    def __init__(self, model: Optional[str] = None):
        self.model = model or Config.OPENAI_MODEL
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.session_manager = SessionManager()

    async def process_user_message(
        self,
        user_message: str,
        user_id: str = "default_user",
        reset_history: bool = False
    ) -> str:
        """
        Unified flow: Single LLM with function calling and context awareness

        Args:
            user_message: User's message text
            user_id: User identifier
            reset_history: If True, clear conversation history

        Returns:
            Bot's response in Hebrew
        """
        if reset_history:
            self.session_manager.clear_session(user_id)

        # Basic validation
        if not user_message or not user_message.strip():
            return "לא קיבלתי הודעה. איך אפשר לעזור לך? 😊"

        try:
            # Get conversation history
            history = self.session_manager.get_history(user_id)

            # Build messages for LLM
            from datetime import datetime
            import pytz
            israel_tz = pytz.timezone('Asia/Jerusalem')
            now = datetime.now(israel_tz)
            hebrew_days = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
            day_name = hebrew_days[now.weekday()]

            # Check if user has active category context
            last_category = self.session_manager.get_last_category(user_id)
            category_context = f"\nContext - Current category: {last_category}" if last_category else ""

            # IMPORTANT: Static instructions FIRST for OpenAI prompt caching (50% discount on cached tokens)
            # Dynamic content (day, category) goes LAST to avoid breaking cache
            system_content = f"""{SYSTEM_INSTRUCTIONS}

---
[CONTEXT]
Today is: {day_name}
You are SaladBot, a helpful customer service assistant for Picnic Maadanim deli. You speak Hebrew only.{category_context}"""

            messages = [{"role": "system", "content": system_content}]
            messages.extend(history[-Config.CHAT_HISTORY_WINDOW_SIZE:] if len(history) > Config.CHAT_HISTORY_WINDOW_SIZE else history)
            messages.append({"role": "user", "content": user_message})

            # Call OpenAI with all available tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[
                    GET_BUSINESS_INFO_TOOL,
                    GET_ORDER_INFO_TOOL,
                    GET_CATEGORY_LIST_TOOL,
                    GET_MENU_ITEMS_TOOL
                ],
                tool_choice="auto",
                temperature=Config.OPENAI_TEMPERATURE
            )

            assistant_message = response.choices[0].message

            # Check if there are tool calls
            if assistant_message.tool_calls:
                # IMPORTANT: Handle ALL tool calls (OpenAI may request multiple)
                # If there are multiple tool calls, we need to respond to each one

                # Check if it's a single static response tool (can bypass second LLM call)
                if len(assistant_message.tool_calls) == 1:
                    first_tool = assistant_message.tool_calls[0]
                    function_name = first_tool.function.name

                    if function_name == "get_business_info":
                        logger.info(f"{{process_user_message}} [Tool Call] get_business_info | User: {user_id}")
                        # Clear category context on greeting
                        self.session_manager.clear_last_category(user_id)
                        final_content = get_business_info_message()

                    elif function_name == "get_order_info":
                        logger.info(f"{{process_user_message}} [Tool Call] get_order_info | User: {user_id}")
                        final_content = get_order_redirect_message()

                    elif function_name == "get_category_list":
                        logger.info(f"{{process_user_message}} [Tool Call] get_category_list | User: {user_id}")
                        # Clear category context when showing general categories
                        self.session_manager.clear_last_category(user_id)
                        final_content = get_category_list_message()

                    elif function_name == "get_menu_items":
                        # Single menu query - process normally
                        final_content = self._handle_single_menu_query(
                            messages, assistant_message, user_id, last_category
                        )

                    else:
                        # Unknown tool
                        logger.error(f"{{process_user_message}} [Tool Error] Unknown tool called: {function_name}")
                        final_content = "מצטערים, אירעה שגיאה. אנא נסה שוב."

                else:
                    # Multiple tool calls - need to handle ALL of them
                    logger.info(f"{{process_user_message}} [Tool Calls] Multiple tools called: {len(assistant_message.tool_calls)} | User: {user_id}")
                    final_content = self._handle_multiple_tool_calls(
                        messages, assistant_message, user_id, last_category
                    )
            else:
                final_content = assistant_message.content

            # Add to session history
            self.session_manager.add_message(user_id, "user", user_message)
            self.session_manager.add_message(user_id, "assistant", final_content)

            return final_content

        except Exception as e:
            logger.error(f"{{process_user_message}} [Exception] Chat service error: {e}", exc_info=True)
            error_msg = f"מצטערים, אירעה שגיאה. אנא נסה שוב."
            return error_msg

    def _handle_single_menu_query(self, messages: list, assistant_msg, user_id: str, last_category: str) -> str:
        """
        Handle a single get_menu_items tool call

        Args:
            messages: Conversation messages list
            assistant_msg: The assistant message with tool_calls
            user_id: User identifier
            last_category: Last browsed category (for context)

        Returns:
            Final AI response
        """
        # Add assistant message with tool call
        messages.append(assistant_msg)

        # Get the first (and only) tool call
        tool_call = assistant_msg.tool_calls[0]
        function_args = json.loads(tool_call.function.arguments)

        logger.info(f"{{_handle_single_menu_query}} [Tool Call] get_menu_items | User: {user_id}")

        # Get category from args or use last category context if not specified
        category = function_args.get("category")
        if not category and last_category:
            category = last_category
            logger.debug(f"{{_handle_single_menu_query}} [Context] Using saved category: {category}")

        # Save category context if provided
        if category:
            self.session_manager.set_last_category(user_id, category)
            logger.debug(f"{{_handle_single_menu_query}} [Context] Saved category: {category}")

        # Get track_shown parameter (defaults to True if not provided)
        track_shown = function_args.get("track_shown", True)
        logger.debug(f"{{_handle_single_menu_query}} [Tracking] track_shown={track_shown}")

        # Determine if user wants details (ingredient queries, specific dish info)
        # When track_shown=False, it means user is asking for DETAILS about specific dishes
        # When track_shown=True, it means user is BROWSING (show minimal info)
        include_details = not track_shown
        logger.debug(f"{{_handle_single_menu_query}} [Display Mode] include_details={include_details}")

        # Only apply exclusion filter if we're tracking shown dishes
        exclude_ids = list(self.session_manager.get_shown_dishes(user_id)) if track_shown else []
        if exclude_ids:
            logger.debug(f"{{_handle_single_menu_query}} [Exclusion] Excluding {len(exclude_ids)} previously shown dishes")

        items = get_menu_items_implementation(
            category=category,
            max_price=function_args.get("max_price"),
            dietary_restriction=function_args.get("dietary_restriction"),
            search_term=function_args.get("search_term"),
            exclude_ids=exclude_ids if exclude_ids else None,
            availability_day=function_args.get("availability_day")
        )

        # Check if we got new items or if all items were already shown
        all_shown = False
        if items:
            dish_ids = [item["id"] for item in items]

            # Only track shown dishes if track_shown=True
            if track_shown:
                # Verify these are actually NEW dishes
                new_dish_ids = [did for did in dish_ids if did not in exclude_ids]

                if new_dish_ids:
                    self.session_manager.add_shown_dishes(user_id, new_dish_ids)
                    total_shown = len(self.session_manager.get_shown_dishes(user_id))
                    logger.info(f"{{_handle_single_menu_query}} [Tracking] Added {len(new_dish_ids)} new dishes | Total shown: {total_shown}")
                else:
                    logger.warning(f"{{_handle_single_menu_query}} [Tracking] All {len(dish_ids)} dishes already shown | Setting all_shown=True")
                    all_shown = True
            else:
                logger.debug(f"{{_handle_single_menu_query}} [Tracking] Skipped tracking (detail mode)")
        else:
            # No items returned - could be truly empty category or all filtered out
            if exclude_ids:
                logger.info(f"{{_handle_single_menu_query}} [Query Result] No new items available (all previously shown)")
                all_shown = True
            else:
                logger.info(f"{{_handle_single_menu_query}} [Query Result] No items match query criteria")

        function_response = format_menu_items_for_ai(items, all_shown=all_shown, include_details=include_details)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": "get_menu_items",
            "content": function_response
        })

        # Get final response from LLM
        second_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=Config.OPENAI_TEMPERATURE
        )

        return second_response.choices[0].message.content

    def _handle_multiple_tool_calls(self, messages: list, assistant_message, user_id: str, last_category: str) -> str:
        """
        Handle multiple tool calls (OpenAI requested multiple functions)

        Args:
            messages: Conversation messages list
            assistant_message: Assistant message with multiple tool_calls
            user_id: User identifier
            last_category: Last browsed category (for context)

        Returns:
            Final AI response
        """
        # Add assistant message with ALL tool calls
        messages.append(assistant_message)

        # Process EACH tool call and add responses
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name

            if function_name == "get_business_info":
                logger.info(f"{{_handle_multiple_tool_calls}} [Tool {tool_call.id}] get_business_info | User: {user_id}")
                response_content = get_business_info_message()

            elif function_name == "get_order_info":
                logger.info(f"{{_handle_multiple_tool_calls}} [Tool {tool_call.id}] get_order_info | User: {user_id}")
                response_content = get_order_redirect_message()

            elif function_name == "get_category_list":
                logger.info(f"{{_handle_multiple_tool_calls}} [Tool {tool_call.id}] get_category_list | User: {user_id}")
                response_content = get_category_list_message()

            elif function_name == "get_menu_items":
                logger.info(f"{{_handle_multiple_tool_calls}} [Tool {tool_call.id}] get_menu_items | User: {user_id}")

                function_args = json.loads(tool_call.function.arguments)

                # Get category from args or use last category context
                category = function_args.get("category") or last_category

                # Save category context
                if category:
                    self.session_manager.set_last_category(user_id, category)

                # For multiple tool calls, use track_shown=False (detail mode)
                # User is asking about multiple specific items/queries
                track_shown = function_args.get("track_shown", False)
                include_details = not track_shown

                # Don't exclude dishes in multi-query mode (user wants full info)
                exclude_ids = []

                items = get_menu_items_implementation(
                    category=category,
                    max_price=function_args.get("max_price"),
                    dietary_restriction=function_args.get("dietary_restriction"),
                    search_term=function_args.get("search_term"),
                    exclude_ids=None,
                    availability_day=function_args.get("availability_day")
                )

                response_content = format_menu_items_for_ai(items, all_shown=False, include_details=include_details)

            else:
                logger.error(f"{{_handle_multiple_tool_calls}} [Tool {tool_call.id}] Unknown tool: {function_name}")
                response_content = "שגיאה: פונקציה לא ידועה"

            # Add tool response for this specific tool_call_id
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": response_content
            })

        # Get final response from LLM after processing ALL tool calls
        logger.info(f"{{_handle_multiple_tool_calls}} [LLM Call] Getting final response for {len(assistant_message.tool_calls)} tool results")

        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=Config.OPENAI_TEMPERATURE
        )

        return final_response.choices[0].message.content
