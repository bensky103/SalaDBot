"""
Configuration Module
Loads and validates environment variables for the SaladBot application
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables"""

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
        print("\n" + "=" * 60)
        print("  SALADBOT CONFIGURATION")
        print("=" * 60)
        print(f"Supabase URL: {cls._mask(cls.SUPABASE_URL)}")
        print(f"Supabase Key: {cls._mask(cls.SUPABASE_KEY)}")
        print(f"OpenAI API Key: {cls._mask(cls.OPENAI_API_KEY)}")
        print(f"WhatsApp Verify Token: {cls._mask(cls.WHATSAPP_VERIFY_TOKEN)}")
        print(f"WhatsApp Access Token: {cls._mask(cls.WHATSAPP_ACCESS_TOKEN)}")
        print(f"WhatsApp Phone Number ID: {cls._mask(cls.WHATSAPP_PHONE_NUMBER_ID)}")
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("=" * 60 + "\n")

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
