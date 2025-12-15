"""
Session Manager for SaladBot
Manages per-user conversation history and shown dishes tracking
"""

from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from collections import deque
from app.config import Config


class SessionManager:
    """
    Manages user sessions with conversation history and shown dishes tracking
    Implements token-efficient context management and dish variety
    """

    def __init__(
        self,
        max_history_messages: Optional[int] = None,
        max_shown_dishes: Optional[int] = None,
        session_timeout_minutes: Optional[int] = None
    ):
        """
        Initialize session manager

        Args:
            max_history_messages: Maximum conversation messages to keep (uses Config if None)
            max_shown_dishes: Maximum shown dish IDs to track (uses Config if None)
            session_timeout_minutes: Session timeout in minutes (uses Config if None)
        """
        self.max_history_messages = max_history_messages or Config.MAX_HISTORY_MESSAGES
        self.max_shown_dishes = max_shown_dishes or Config.MAX_SHOWN_DISHES_TRACKED
        self.session_timeout = timedelta(minutes=session_timeout_minutes or Config.SESSION_TIMEOUT_MINUTES)

        # Store per-user data
        # Format: {user_id: {"history": deque, "shown_dishes": set, "last_activity": datetime, "last_category": str, "last_category_time": datetime}}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def _cleanup_expired_sessions(self):
        """Remove expired sessions to prevent memory bloat"""
        now = datetime.now()
        expired_users = [
            user_id
            for user_id, session_data in self.sessions.items()
            if now - session_data["last_activity"] > self.session_timeout
        ]

        for user_id in expired_users:
            del self.sessions[user_id]

    def _get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        """Get or create session for user"""
        self._cleanup_expired_sessions()

        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "history": deque(maxlen=self.max_history_messages),
                "shown_dishes": set(),
                "last_activity": datetime.now(),
                "last_category": None,
                "last_category_time": None
            }

        # Update last activity
        self.sessions[user_id]["last_activity"] = datetime.now()
        return self.sessions[user_id]

    def add_message(self, user_id: str, role: str, content: str):
        """
        Add a message to user's conversation history

        Args:
            user_id: User identifier (WhatsApp ID)
            role: Message role (user/assistant/system)
            content: Message content
        """
        session = self._get_or_create_session(user_id)
        session["history"].append({"role": role, "content": content})

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for user

        Args:
            user_id: User identifier

        Returns:
            List of message dictionaries with role and content
        """
        session = self._get_or_create_session(user_id)
        return list(session["history"])

    def add_shown_dishes(self, user_id: str, dish_ids: List[int]):
        """
        Add dish IDs to user's shown dishes set

        Args:
            user_id: User identifier
            dish_ids: List of dish IDs that were shown
        """
        session = self._get_or_create_session(user_id)
        shown_set = session["shown_dishes"]

        # Add new dish IDs
        shown_set.update(dish_ids)

        # Limit set size (keep most recent)
        if len(shown_set) > self.max_shown_dishes:
            # Convert to list, keep last N items, convert back to set
            shown_list = list(shown_set)
            session["shown_dishes"] = set(shown_list[-self.max_shown_dishes:])

    def get_shown_dishes(self, user_id: str) -> Set[int]:
        """
        Get set of dish IDs already shown to user

        Args:
            user_id: User identifier

        Returns:
            Set of dish IDs
        """
        session = self._get_or_create_session(user_id)
        return session["shown_dishes"].copy()

    def reset_shown_dishes(self, user_id: str):
        """
        Reset shown dishes for user (when they've seen too many or request it)

        Args:
            user_id: User identifier
        """
        session = self._get_or_create_session(user_id)
        session["shown_dishes"].clear()

    def clear_session(self, user_id: str):
        """
        Clear entire session for user

        Args:
            user_id: User identifier
        """
        if user_id in self.sessions:
            del self.sessions[user_id]

    def set_last_category(self, user_id: str, category: str):
        """
        Set the last browsed category for context preservation
        
        Args:
            user_id: User identifier
            category: Category name (e.g., 'סלטים', 'קינוחים')
        """
        session = self._get_or_create_session(user_id)
        session["last_category"] = category
        session["last_category_time"] = datetime.now()
    
    def get_last_category(self, user_id: str, timeout_minutes: Optional[int] = None) -> Optional[str]:
        """
        Get the last browsed category if still valid

        Args:
            user_id: User identifier
            timeout_minutes: How long to keep category context (uses Config if None)

        Returns:
            Category name or None if expired/not set
        """
        session = self._get_or_create_session(user_id)
        last_category = session.get("last_category")
        last_category_time = session.get("last_category_time")

        # Return None if no category set
        if not last_category or not last_category_time:
            return None

        # Use config value if not specified
        timeout = timeout_minutes or Config.CATEGORY_CONTEXT_TIMEOUT_MINUTES

        # Check if expired
        if datetime.now() - last_category_time > timedelta(minutes=timeout):
            self.clear_last_category(user_id)
            return None

        return last_category
    
    def clear_last_category(self, user_id: str):
        """
        Clear the last category context
        
        Args:
            user_id: User identifier
        """
        session = self._get_or_create_session(user_id)
        session["last_category"] = None
        session["last_category_time"] = None

    def get_session_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get session info for debugging

        Args:
            user_id: User identifier

        Returns:
            Dictionary with session statistics
        """
        if user_id not in self.sessions:
            return {
                "exists": False,
                "message_count": 0,
                "shown_dishes_count": 0
            }

        session = self.sessions[user_id]
        return {
            "exists": True,
            "message_count": len(session["history"]),
            "shown_dishes_count": len(session["shown_dishes"]),
            "last_activity": session["last_activity"].isoformat(),
            "last_category": session.get("last_category")
        }
