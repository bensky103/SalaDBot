"""
Utility Functions
Helper functions for date/time, logging, and other common operations
"""

import logging
from datetime import datetime
from typing import Optional, List


# Logging Configuration
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger("saladbot")
    return logger


# Date/Time Utilities for Availability Checking

def get_current_day_hebrew() -> str:
    """
    Get current day of week in Hebrew format

    Returns:
        Hebrew day name (e.g., "א", "ב", "ג", "ד", "ה", "ו", "ש")
    """
    day_mapping = {
        0: "ב",  # Monday
        1: "ג",  # Tuesday
        2: "ד",  # Wednesday
        3: "ה",  # Thursday
        4: "ו",  # Friday
        5: "ש",  # Saturday
        6: "א",  # Sunday
    }

    today = datetime.now().weekday()
    return day_mapping[today]


def get_current_day_english() -> str:
    """
    Get current day of week in English (short form)

    Returns:
        English day abbreviation (e.g., "Sun", "Mon", "Tue")
    """
    day_mapping = {
        0: "Mon",
        1: "Tue",
        2: "Wed",
        3: "Thu",
        4: "Fri",
        5: "Sat",
        6: "Sun",
    }

    today = datetime.now().weekday()
    return day_mapping[today]


def parse_hebrew_day_range(availability_days: str) -> List[str]:
    """
    Parse Hebrew day range string into list of day abbreviations

    Args:
        availability_days: String like "ימים ד - ו" or "ד ה ו"

    Returns:
        List of Hebrew day abbreviations (e.g., ["ד", "ה", "ו"])
    """
    if not availability_days:
        return []

    # Hebrew day order: א (Sun), ב (Mon), ג (Tue), ד (Wed), ה (Thu), ו (Fri), ש (Sat)
    day_order = ["א", "ב", "ג", "ד", "ה", "ו", "ש"]

    # Check for range pattern like "ימים ד - ו" or "ד - ו"
    if " - " in availability_days or "- " in availability_days or " -" in availability_days:
        # Extract the day letters
        parts = availability_days.replace("ימים", "").replace("יום", "").strip().split("-")
        if len(parts) == 2:
            start_day = parts[0].strip()
            end_day = parts[1].strip()

            # Find indices in day_order
            try:
                start_idx = day_order.index(start_day)
                end_idx = day_order.index(end_day)

                # Generate range (handle wrap-around if needed)
                if start_idx <= end_idx:
                    return day_order[start_idx:end_idx + 1]
                else:
                    # Wrap around week (e.g., ו - ב means Fri, Sat, Sun, Mon, Tue)
                    return day_order[start_idx:] + day_order[:end_idx + 1]
            except ValueError:
                # If day not found, return empty
                pass

    # Check for space-separated days like "ד ה ו"
    # Extract all Hebrew letters that match day abbreviations
    days_found = [day for day in day_order if day in availability_days]
    if days_found:
        return days_found

    return []


def is_item_available_today(availability_days: Optional[str]) -> bool:
    """
    Check if an item is available today based on availability_days field

    Args:
        availability_days: String like "ימים ד - ו" or "Sun-Thu" or None

    Returns:
        True if available today, False otherwise
    """
    if not availability_days:
        # If no availability specified, assume always available
        return True

    current_day_hebrew = get_current_day_hebrew()
    current_day_english = get_current_day_english()

    # Try parsing Hebrew day range
    hebrew_days = parse_hebrew_day_range(availability_days)
    if hebrew_days and current_day_hebrew in hebrew_days:
        return True

    # Check if current day appears in the availability string (fallback)
    availability_lower = availability_days.lower()

    # English format check (e.g., "Mon-Fri", "Wed")
    if current_day_english.lower() in availability_lower:
        return True

    return False


def format_phone_number(phone: str) -> str:
    """
    Format phone number for WhatsApp API
    Ensures proper format (no + or spaces)

    Args:
        phone: Phone number in various formats

    Returns:
        Formatted phone number
    """
    # Remove common separators
    cleaned = phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    return cleaned


def truncate_message(message: str, max_length: int = 4096) -> str:
    """
    Truncate message to WhatsApp's maximum length

    Args:
        message: Original message
        max_length: Maximum allowed length (WhatsApp limit is 4096 characters)

    Returns:
        Truncated message if needed
    """
    if len(message) <= max_length:
        return message

    # Truncate and add ellipsis
    return message[:max_length - 3] + "..."


def mask_sensitive_data(data: str, show_chars: int = 4) -> str:
    """
    Mask sensitive data for logging

    Args:
        data: Sensitive string to mask
        show_chars: Number of characters to show at start and end

    Returns:
        Masked string
    """
    if not data:
        return "[EMPTY]"

    if len(data) <= show_chars * 2:
        return "***"

    return f"{data[:show_chars]}...{data[-show_chars:]}"


# Error Message Helpers

def get_hebrew_error_message(error_type: str = "general") -> str:
    """
    Get user-friendly Hebrew error messages

    Args:
        error_type: Type of error (general, database, api, etc.)

    Returns:
        Hebrew error message
    """
    error_messages = {
        "general": "מצטערים, אירעה שגיאה. אנא נסה שוב.",
        "database": "מצטערים, לא ניתן לגשת לתפריט כרגע. אנא נסה שוב מאוחר יותר.",
        "api": "מצטערים, השירות אינו זמין כרגע. אנא נסה שוב בעוד מספר דקות.",
        "timeout": "מצטערים, הבקשה לקחה יותר מדי זמן. אנא נסה שוב.",
    }

    return error_messages.get(error_type, error_messages["general"])


# Validation Helpers

def is_valid_whatsapp_id(wa_id: str) -> bool:
    """
    Validate WhatsApp ID format (phone number)

    Args:
        wa_id: WhatsApp ID to validate

    Returns:
        True if valid format, False otherwise
    """
    # Basic validation: should be numeric and reasonable length (10-15 digits)
    cleaned = wa_id.replace("+", "").replace(" ", "")
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


# Message Detection Helpers

def is_greeting_or_generic(message: str) -> bool:
    """
    Detect if message is ONLY a greeting or very generic query (no specific menu query)

    Returns True only if the message doesn't contain substantive questions about menu items.
    This allows "היי, מה יש לכם טבעוני?" to be processed as a menu query, not a greeting.

    Args:
        message: User message

    Returns:
        True if ONLY greeting/generic (should get business info), False otherwise
    """
    message_lower = message.lower().strip()

    # Remove common punctuation for cleaner matching
    message_clean = message_lower.replace("?", "").replace("!", "").replace(",", "").strip()

    # Check if message is very short (likely just a greeting)
    if len(message_clean) <= 4:
        return True

    # Keywords that indicate a substantive menu query (NOT just greeting)
    substantive_keywords = [
        "מנות", "סלט", "בשר", "עוף", "דג", "קינוח", "מאפה", "מרק",
        "טבעוני", "גלוטן", "אלרגיה", "רגיש", "מחיר", "עולה", "עולות",
        "קטגורי", "תפריט", "יש לכם", "יש בתפריט", "מה אפשר",
        "זמין", "יום", "שישי", "חמישי", "ביום", "היום",
        "אגוז", "חלב", "ביצ", "שומשום", "סויה", "ללא", "בלי",
        "ממרח", "גבינ", "חומוס", "פלאפל", "חציל", "חמוצ"
    ]

    # If message contains substantive keywords, it's NOT just a greeting
    for keyword in substantive_keywords:
        if keyword in message_lower:
            return False

    # Pure greetings (exact matches or very close)
    pure_greetings = [
        "שלום", "היי", "הי", "בוקר טוב", "ערב טוב", "צהריים טובים",
        "מה נשמע", "מה קורה", "אהלן", "ברוך הבא", "hello", "hi", "hey"
    ]

    # Generic queries without specific menu content (should trigger business info)
    generic_queries = [
        "מה זה", "ספר לי", "תספר לי", "מידע", "מי אתם",
        "מה אתם", "תסביר", "תסביר לי", "מה פה", "תספר"
    ]

    # Check if message is ONLY a greeting/generic (exact match or starts with)
    all_patterns = pure_greetings + generic_queries
    for pattern in all_patterns:
        # Exact match
        if message_clean == pattern:
            return True
        # Starts with pattern and remainder is very short (e.g., "שלום!" or "היי בוקר טוב")
        if message_clean.startswith(pattern):
            remainder = message_clean[len(pattern):].strip()
            # If remainder is empty or just another greeting, it's still generic
            if len(remainder) <= 10:  # Allow for short greeting combinations
                return True

    return False


def is_allergen_query(message: str) -> bool:
    """
    Detect if user is asking about allergens or has allergy concerns

    Args:
        message: User message

    Returns:
        True if allergen-related query, False otherwise
    """
    message_lower = message.lower().strip()

    # Allergen-related keywords
    allergen_keywords = [
        "אלרגיה", "אלרגי", "רגיש", "רגישות", "עלול", "עלולה",
        "בטוח", "בטוחה", "מכיל", "מכילה", "אגוז", "אגוזים",
        "גלוטן", "חלב", "ביצ", "שומשום", "סויה", "דגים",
        "allergy", "allergic", "safe", "contain"
    ]

    for keyword in allergen_keywords:
        if keyword in message_lower:
            return True

    return False


def is_general_menu_query(message: str) -> bool:
    """
    Detect if user is asking for general menu info (should list categories)

    Args:
        message: User message

    Returns:
        True if general menu query, False otherwise
    """
    message_lower = message.lower().strip()

    # Remove punctuation for cleaner matching
    message_clean = message_lower.replace("?", "").replace("!", "").replace(",", "").strip()

    # CHECK GENERAL PATTERNS FIRST (highest priority)
    # Patterns that indicate wanting to see all categories/general overview
    general_patterns = [
        "איזה קטגוריות", "קטגוריות יש", "קטגוריות",
        "מה יש לכם", "מה יש בתפריט", "מה אפשר להזמין",
        "תפריט", "רשימה של", "מה אתם מציעים",
        "איזה מנות יש לכם", "איזה מנות", "מה המנות", "מה הקטגוריות"
    ]

    # Check for matches first (check in cleaned message for better detection)
    for pattern in general_patterns:
        if pattern in message_clean:
            return True

    # If message mentions "contains/with" an ingredient, it's a specific query
    ingredient_search_patterns = [
        "מכיל", "מכילות", "שיש בהם", "שיש בו", "עם ", "גזר", "בטטה",
        "תפוח", "עגבני", "מלפפון", "בצל", "שום", "תירס"
    ]

    for pattern in ingredient_search_patterns:
        if pattern in message_lower:
            return False  # Looking for dishes with specific ingredient

    # If message mentions specific items/categories/restrictions, it's NOT general
    specific_items = [
        "חומוס", "פלאפל", "חציל",
        "טבעוני", "גלוטן", "מחיר", "ביום", "אגוזים", "חלב",
        "אלרגיה", "ללא", "בלי", "רגיש",
        # Specific categories
        "בשר", "עוף", "דג", "דגים", "סלט", "סלטים", "קינוח", "קינוחים",
        "מאפה", "מאפים", "לחם", "לחמים", "מרק", "מרקים", "גבינ", "ממרח",
        "פשטידות", "טוגנים", "חמוצ", "תוספות", "קרקר", "עוגיות", "שישי"
    ]

    for item in specific_items:
        if item in message_lower:
            return False  # Specific query, not general

    return False


def get_business_info_message() -> str:
    """
    Get the standard business information message

    Returns:
        Hebrew business info message
    """
    return """שלום! ברוכים הבאים לפיקניק מעדנים 👋

אנחנו עסק משפחתי עם מסורת של יותר מ-50 שנים בגבעתיים. מאז 1969 אנחנו מתמחים בייצור אוכל מוכן וסלטים טריים, ביתיים ואיכותיים, עם חומרי הגלם הכי טובים והקפדה על טעם, ניקיון ושירות מצוין.

יש לנו מבחר עשיר של:
• מנות עיקריות וסלטים (מעל 150 סוגים!)
• מנות טבעוניות וללא גלוטן
• גבינות ודגים מעושנים
• מאפים, מרקים וקינוחים
• אוכל לאירועים קטנים וארוחות מוכנות לארגונים

⏰ שעות פעילות:
א-ד: 8:00-19:00 | ה: 8:00-20:00 | ו: 6:30-15:00

איך אני יכול לעזור לך היום? אפשר לשאול על מנות ספציפיות, קטגוריות, או כל שאלה אחרת!

להזמנה: https://order.picnicmaadanim.co.il"""


def get_category_list_message() -> str:
    """
    Get message listing all available categories

    Returns:
        Hebrew category listing message
    """
    return """יש לנו מבחר גדול של מנות! איזו קטגוריה מעניינת אותך?

📋 הקטגוריות שלנו:
• סלטים - מעל 150 סוגי סלטים טריים
• בשר - מנות בשר ביתיות מוכנות
• עוף - מנות עוף מוכנות
• דגים - מנות דגים טריות
• סלטי דגים - סלטים מבוססי דגים
• דג מעושן - דגים מעושנים
• גבינות - מבחר גבינות
• ממרחים - ממרחים ביתיים
• מאפים - לחמים ומאפים טריים
• פשטידות - פשטידות ביתיות
• מרקים - מרקים חמים
• טוגנים - מאכלים מטוגנים
• חמוצים - מלפפונים וירקות חמוצים
• תוספות - תוספות למנות
• קינוחים - קינוחים מתוקים
• קרקרים - קרקרים ופריכיות
• עוגיות - עוגיות ביתיות
• טבעוני - מנות טבעוניות
• ספיישל שישי - מנות מיוחדות ליום שישי

ספר לי איזו קטגוריה מעניינת אותך ואציג לך מנות ספציפיות!"""


def get_allergen_safety_message() -> str:
    """
    Get safety message for allergen queries when few/no items are safe

    Returns:
        Hebrew safety message about shared kitchen
    """
    return """מצטערים, רוב המנות שלנו מיוצרות במטבח משותף ועלולות להכיל עקבות של אלרגנים שונים.

לבטיחותך, אנו ממליצים ליצור קשר ישירות עם המסעדה לקבלת ייעוץ אישי והמלצות ספציפיות.

📞 ניתן ליצור קשר בשעות הפעילות:
• א-ד: 8:00-19:00
• ה: 8:00-20:00
• ו: 6:30-15:00

בטיחותך חשובה לנו מאוד! 🛡️"""
