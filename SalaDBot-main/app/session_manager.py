"""
Session Manager for SaladBot
Manages per-user conversation history and shown dishes tracking
"""

from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from collections import deque


class SessionManager:
    """
    Manages user sessions with conversation history and shown dishes tracking
    Implements token-efficient context management and dish variety
    """

    def __init__(
        self,
        max_history_messages: int = 10,  # Last 5 exchanges (10 messages)
        max_shown_dishes: int = 20,  # Track last 20 shown dishes
        session_timeout_minutes: int = 30  # Session expires after 30 min
    ):
        """
        Initialize session manager

        Args:
            max_history_messages: Maximum conversation messages to keep
            max_shown_dishes: Maximum shown dish IDs to track
            session_timeout_minutes: Session timeout in minutes
        """
        self.max_history_messages = max_history_messages
        self.max_shown_dishes = max_shown_dishes
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

        # Store per-user data
        # Format: {user_id: {"history": deque, "shown_dishes": set, "last_activity": datetime, "current_category": str, "category_total": int}}
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
                "current_category": None,
                "category_total": 0,
                "category_shown_dishes": set()  # Track dishes shown for current category
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

    def set_category_context(self, user_id: str, category: Optional[str], total_count: int):
        """
        Set current category context for dish counter
        If category changes, resets category-specific shown dishes

        Args:
            user_id: User identifier
            category: Category being queried (None to clear)
            total_count: Total dishes in this category
        """
        session = self._get_or_create_session(user_id)

        # If category changed, reset category-specific tracking
        if session.get("current_category") != category:
            session["category_shown_dishes"] = set()

        session["current_category"] = category
        session["category_total"] = total_count if category else 0

    def get_category_context(self, user_id: str) -> tuple[Optional[str], int]:
        """
        Get current category context

        Args:
            user_id: User identifier

        Returns:
            Tuple of (category, total_count)
        """
        session = self._get_or_create_session(user_id)
        return session.get("current_category"), session.get("category_total", 0)

    def add_category_shown_dishes(self, user_id: str, dish_ids: List[int]):
        """
        Add dishes to category-specific shown dishes counter

        Args:
            user_id: User identifier
            dish_ids: List of dish IDs shown in current category
        """
        session = self._get_or_create_session(user_id)
        session["category_shown_dishes"].update(dish_ids)

    def get_category_shown_count(self, user_id: str) -> int:
        """
        Get count of dishes shown in current category

        Args:
            user_id: User identifier

        Returns:
            Number of dishes shown in current category
        """
        session = self._get_or_create_session(user_id)
        return len(session.get("category_shown_dishes", set()))

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
            "current_category": session.get("current_category"),
            "category_total": session.get("category_total", 0)
        }
