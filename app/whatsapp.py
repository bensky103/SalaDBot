"""
WhatsApp Integration Module
Handles message parsing, sending, and webhook verification
"""

import requests
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
from app.config import config
from app.models import (
    WhatsAppWebhookPayload,
    WhatsAppTextRequest,
    WhatsAppMessageResponse,
    BotRequest
)

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Client for interacting with WhatsApp Cloud API"""

    def __init__(self):
        self.access_token = config.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = config.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def send_text_message(self, to: str, message: str) -> bool:
        """
        Send a text message via WhatsApp Cloud API

        Args:
            to: Recipient WhatsApp ID (phone number)
            message: Message text to send

        Returns:
            True if message sent successfully, False otherwise
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=config.WHATSAPP_API_TIMEOUT_SECONDS)
            response.raise_for_status()

            logger.info(f"Message sent successfully to {to}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp message to {to}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False

    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read (optional feature)

        Args:
            message_id: WhatsApp message ID

        Returns:
            True if marked successfully, False otherwise
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=config.WHATSAPP_API_TIMEOUT_SECONDS)
            response.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to mark message {message_id} as read: {str(e)}")
            return False


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature from WhatsApp (security feature)

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value

    Returns:
        True if signature is valid, False otherwise
    """
    # If no app secret is configured, skip verification
    if not config.WHATSAPP_APP_SECRET:
        logger.warning("Webhook signature verification skipped (no app secret configured)")
        return True

    # If no signature provided, skip verification (for backwards compatibility)
    if not signature:
        logger.warning("No signature provided in webhook request")
        return True

    try:
        # WhatsApp sends signature as "sha256=<hash>"
        expected_signature = hmac.new(
            key=config.WHATSAPP_APP_SECRET.encode(),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()

        expected_sig_header = f"sha256={expected_signature}"

        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_sig_header, signature)

        if is_valid:
            logger.info("Webhook signature verified successfully")
        else:
            logger.error(f"Webhook signature verification failed. Expected: {expected_sig_header[:20]}..., Got: {signature[:20]}...")

        return is_valid

    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False


def parse_webhook_payload(payload: Dict[str, Any]) -> Optional[BotRequest]:
    """
    Parse incoming WhatsApp webhook payload and extract message details

    Args:
        payload: Raw webhook payload dictionary

    Returns:
        BotRequest object if valid text message found, None otherwise
    """
    try:
        # Log minimal info for performance (payload can be huge)
        logger.info("Parsing webhook payload")

        # Validate payload structure using Pydantic
        webhook = WhatsAppWebhookPayload(**payload)

        # Extract first entry (usually only one)
        if not webhook.entry:
            logger.warning("No entries in webhook payload")
            return None

        entry = webhook.entry[0]

        # Extract first change (usually only one)
        if not entry.changes:
            logger.warning("No changes in webhook entry")
            return None

        change = entry.changes[0]
        value = change.value

        # Check if there are messages
        if not value.messages:
            logger.info("No messages in webhook payload (might be status update)")
            return None

        # Extract first message
        message = value.messages[0]

        # Only process text messages
        if message.type != "text" or not message.text:
            logger.info(f"Non-text message received (type: {message.type})")
            return None

        # Extract sender info
        user_id = message.from_
        message_text = message.text.body
        message_id = message.id

        logger.info(f"Parsed message from {user_id}: {message_text[:50]}...")

        return BotRequest(
            user_id=user_id,
            message=message_text,
            message_id=message_id
        )

    except Exception as e:
        logger.error(f"Error parsing webhook payload: {str(e)}", exc_info=True)
        logger.error(f"Problematic payload: {payload}")
        return None


def send_error_message(to: str, error_type: str = "general") -> None:
    """
    Send a user-friendly error message in Hebrew

    Args:
        to: Recipient WhatsApp ID
        error_type: Type of error (general, database, api, timeout)
    """
    from app.utils import get_hebrew_error_message

    client = WhatsAppClient()
    error_message = get_hebrew_error_message(error_type)
    client.send_text_message(to, error_message)


# Export main client instance
whatsapp_client = WhatsAppClient()
