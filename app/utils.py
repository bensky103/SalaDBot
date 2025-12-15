"""
Utility Functions
Helper functions for logging, security, and message formatting
"""

import logging
from typing import Optional
from app.config import Config


# Logging Configuration
def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the application

    Args:
        log_level: Logging level (uses Config if None)

    Returns:
        Configured logger instance
    """
    level = log_level or Config.LOG_LEVEL
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Mute noisy HTTP libraries
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger(Config.LOGGER_NAME)
    return logger


# Message Detection Helpers
# Note: Hard-coded pattern matching removed - LLM handles intent detection naturally via instructions.txt


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

אני בוט מידע שכאן כדי לעזור לך למצוא מנות ולענות על שאלות לגבי התפריט שלנו 😊

אנחנו עסק משפחתי עם מסורת של יותר מ-50 שנים בגבעתיים. מאז 1969 אנחנו מתמחים בייצור אוכל מוכן וסלטים טריים, ביתיים ואיכותיים, עם חומרי הגלם הכי טובים והקפדה על טעם, ניקיון ושירות מצוין.

🍽️ יש לנו מבחר עשיר של:
🥗 מנות עיקריות וסלטים (מעל 150 סוגים!)
🌱 מנות טבעוניות וללא גלוטן
🧀 גבינות ו🐟 דגים מעושנים
🥖 מאפים, 🍲 מרקים ו🍰 קינוחים
🎉 אוכל לאירועים קטנים וארוחות מוכנות לארגונים

⏰ שעות פעילות:
א-ד: 8:00-19:00 | ה: 8:00-20:00 | ו: 6:30-15:00

איך אני יכול לעזור לך היום? אפשר לשאול על מנות ספציפיות, קטגוריות, או כל שאלה אחרת!

🌐 לאתר: https://picnicmaadanim.co.il/

🛒 להזמנה: https://order.picnicmaadanim.co.il\n
"""


def get_category_list_message() -> str:
    """
    Get message listing all available categories

    Returns:
        Hebrew category listing message
    """
    return """יש לנו מבחר גדול של מנות! איזו קטגוריה מעניינת אותך?

📋 הקטגוריות שלנו:

🥗 **סלטים ומנות עיקריות:**
🥗 סלטים - מעל 165 סוגים! (חציל, חומוס, טחינה, דגים, גזר, כרוב ועוד)
🥩 בשר - מנות בשר ביתיות מוכנות
🍗 עוף - מנות עוף מוכנות
🐟 דגים - מנות דגים טריות
🐠 סלטי דגים - סלטים מבוססי דגים
🎣 דג מעושן - דגים מעושנים
🌱 טבעוני - מנות טבעוניות

🧀 **מוצרי חלב וממרחים:**
🧀 גבינות - מבחר גבינות
🥫 ממרחים - ממרחים ביתיים

🥖 **מאפים ומוצרי בצק:**
🥖 מאפים - לחמים ומאפים טריים (קרואסונים, בורקסים)
🥧 פשטידות - פשטידות ביתיות

🍲 **מרקים ותוספות:**
🍲 מרקים - מרקים חמים
🍤 טוגנים - מאכלים מטוגנים
🥒 חמוצים - מלפפונים וירקות חמוצים
🍚 תוספות - תוספות למנות

🍰 **קטגוריות מתוקות:**
🍰 קינוחים - עוגות, מוסים, טירמיסו (לא עוגיות!)
🍩 עוגיות - עוגיות וביסקוויטים בלבד
🍪 קרקרים - קרקרים ופריכיות

✨ **מיוחדים:**
✨ ספיישל שישי - מנות מיוחדות ליום שישי

ספר לי איזו קטגוריה מעניינת אותך ואציג לך מנות ספציפיות!"""
