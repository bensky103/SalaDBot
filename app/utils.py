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
# Note: Hard-coded pattern matching removed - router (ChatService.classify_intent) handles intent classification


def get_order_redirect_message() -> str:
    """
    Get the order redirect message with warm tone

    Returns:
        Hebrew order redirect message
    """
    return """אשמח לעזור! 😊

אני בוט מידע שכאן כדי לעזור לך למצוא מנות ולענות על שאלות לגבי התפריט שלנו.

כדי להזמין, אשמח להפנות אותך לאתר ההזמנות שלנו:
🌐 https://order.picnicmaadanim.co.il

יש לך שאלות נוספות לגבי המנות שלנו? אני כאן לעזור! 😊"""


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

לאתר: https://picnicmaadanim.co.il/

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
