"""
Configuration Module
Centralized configuration for the SaladBot application
All configurable parameters are defined here for easy management
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration - all tunable parameters in one place"""

    # ========================================================================
    # ENVIRONMENT VARIABLES (API Keys & Secrets)
    # ========================================================================

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # WhatsApp Configuration
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_APP_SECRET: str = os.getenv("WHATSAPP_APP_SECRET", "")

    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ========================================================================
    # SESSION & TIMEOUT CONFIGURATION
    # ========================================================================

    # Session timeout - how long before a user session expires (minutes)
    SESSION_TIMEOUT_MINUTES: int = 30

    # Category context timeout - how long to remember user's browsing category (minutes)
    CATEGORY_CONTEXT_TIMEOUT_MINUTES: int = 10

    # WhatsApp API request timeout (seconds)
    WHATSAPP_API_TIMEOUT_SECONDS: int = 10

    # ========================================================================
    # MESSAGE & HISTORY LIMITS
    # ========================================================================

    # Maximum conversation messages to keep in session storage
    # Increased to 50 to support 20-exchange context window (40 messages + buffer)
    MAX_HISTORY_MESSAGES: int = 50

    # Number of messages to include in LLM context (last N messages)
    # This is the conversation window sent to OpenAI
    # Note: With 2 messages per exchange (user + assistant), 40 messages = 20 exchanges
    # This ensures context is never lost during a conversation session
    CHAT_HISTORY_WINDOW_SIZE: int = 40

    # Maximum user input message length (characters)
    MAX_USER_INPUT_LENGTH: int = 500

    # WhatsApp message length limit (characters)
    WHATSAPP_MESSAGE_MAX_LENGTH: int = 4096

    # ========================================================================
    # DISH/MENU QUERY LIMITS
    # ========================================================================

    # Maximum number of shown dish IDs to track (for variety/anti-repetition)
    MAX_SHOWN_DISHES_TRACKED: int = 20

    # Database fetch limit when excluding previously shown dishes
    DB_FETCH_LIMIT_WITH_EXCLUSIONS: int = 10

    # Database fetch limit when no exclusions needed
    DB_FETCH_LIMIT_NO_EXCLUSIONS: int = 5

    # Maximum number of dishes to return to user in final result
    MAX_DISHES_RETURNED: int = 5

    # Threshold for "few results" warning on allergen queries
    ALLERGEN_FEW_RESULTS_THRESHOLD: int = 2

    # ========================================================================
    # AI MODEL CONFIGURATION
    # ========================================================================

    # OpenAI model to use for chat completions
    # Options: "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", etc.
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Temperature for AI responses (0.0 = deterministic, 1.0 = creative)
    # Set to 0.0 for maximum consistency and to prevent hallucination/mixing of data
    # Especially important when synthesizing multiple tool responses
    OPENAI_TEMPERATURE: float = 0.0

    # ========================================================================
    # SERVER CONFIGURATION
    # ========================================================================

    # FastAPI server port
    SERVER_PORT: int = int(os.getenv("PORT", "8000"))

    # Logging identifier prefix
    LOGGER_NAME: str = "saladbot"

    # ========================================================================
    # DEBUGGING & LOGGING
    # ========================================================================

    # Number of excluded dish IDs to show in debug logs
    DEBUG_EXCLUDED_IDS_SHOW_COUNT: int = 10

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required environment variables are set

        Returns:
            True if all required variables are present, False otherwise
        """
        required_vars = {
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
        }

        missing_vars = [name for name, value in required_vars.items() if not value]

        if missing_vars:
            print(f"[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
            return False

        print("[OK] All required environment variables are set")
        return True

    @classmethod
    def validate_whatsapp(cls) -> bool:
        """
        Validate WhatsApp-specific environment variables
        (Optional for development, required for production)

        Returns:
            True if all WhatsApp variables are present, False otherwise
        """
        whatsapp_vars = {
            "WHATSAPP_VERIFY_TOKEN": cls.WHATSAPP_VERIFY_TOKEN,
            "WHATSAPP_ACCESS_TOKEN": cls.WHATSAPP_ACCESS_TOKEN,
            "WHATSAPP_PHONE_NUMBER_ID": cls.WHATSAPP_PHONE_NUMBER_ID,
        }

        missing_vars = [name for name, value in whatsapp_vars.items() if not value]

        if missing_vars:
            print(f"[WARNING] Missing WhatsApp environment variables: {', '.join(missing_vars)}")
            print("   WhatsApp integration will not work without these.")
            return False

        print("[OK] All WhatsApp environment variables are set")
        return True

    @classmethod
    def print_config(cls) -> None:
        """Print configuration (with sensitive data masked)"""
        print("\n" + "=" * 70)
        print("  SALADBOT CONFIGURATION")
        print("=" * 70)

        print("\n[API CREDENTIALS]")
        print(f"  Supabase URL: {cls._mask(cls.SUPABASE_URL)}")
        print(f"  Supabase Key: {cls._mask(cls.SUPABASE_KEY)}")
        print(f"  OpenAI API Key: {cls._mask(cls.OPENAI_API_KEY)}")
        print(f"  WhatsApp Verify Token: {cls._mask(cls.WHATSAPP_VERIFY_TOKEN)}")
        print(f"  WhatsApp Access Token: {cls._mask(cls.WHATSAPP_ACCESS_TOKEN)}")
        print(f"  WhatsApp Phone Number ID: {cls._mask(cls.WHATSAPP_PHONE_NUMBER_ID)}")

        print("\n[SESSION & TIMEOUTS]")
        print(f"  Session Timeout: {cls.SESSION_TIMEOUT_MINUTES} minutes")
        print(f"  Category Context Timeout: {cls.CATEGORY_CONTEXT_TIMEOUT_MINUTES} minutes")
        print(f"  WhatsApp API Timeout: {cls.WHATSAPP_API_TIMEOUT_SECONDS} seconds")

        print("\n[MESSAGE & HISTORY]")
        print(f"  Max History Messages: {cls.MAX_HISTORY_MESSAGES}")
        print(f"  Chat History Window Size: {cls.CHAT_HISTORY_WINDOW_SIZE}")
        print(f"  Max User Input Length: {cls.MAX_USER_INPUT_LENGTH} chars")
        print(f"  WhatsApp Message Max: {cls.WHATSAPP_MESSAGE_MAX_LENGTH} chars")

        print("\n[DISH/MENU QUERIES]")
        print(f"  Max Shown Dishes Tracked: {cls.MAX_SHOWN_DISHES_TRACKED}")
        print(f"  DB Fetch Limit (with exclusions): {cls.DB_FETCH_LIMIT_WITH_EXCLUSIONS}")
        print(f"  DB Fetch Limit (no exclusions): {cls.DB_FETCH_LIMIT_NO_EXCLUSIONS}")
        print(f"  Max Dishes Returned: {cls.MAX_DISHES_RETURNED}")
        print(f"  Allergen Few Results Threshold: {cls.ALLERGEN_FEW_RESULTS_THRESHOLD}")

        print("\n[AI MODEL]")
        print(f"  OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"  Temperature: {cls.OPENAI_TEMPERATURE}")

        print("\n[SERVER & DEBUG]")
        print(f"  Server Port: {cls.SERVER_PORT}")
        print(f"  Debug Mode: {cls.DEBUG}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Logger Name: {cls.LOGGER_NAME}")

        print("=" * 70 + "\n")

    @staticmethod
    def _mask(value: str) -> str:
        """Mask sensitive values for display"""
        if not value:
            return "[NOT SET]"
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"


# Export config instance
config = Config()


if __name__ == "__main__":
    # Test configuration when run directly
    config.print_config()
    config.validate()
    config.validate_whatsapp()
