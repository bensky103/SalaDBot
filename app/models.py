"""
Pydantic Models for WhatsApp Webhook Payloads
Defines data structures for incoming/outgoing WhatsApp messages
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# WhatsApp Webhook Models (Incoming Messages)

class WhatsAppProfile(BaseModel):
    """WhatsApp user profile information"""
    name: str


class WhatsAppContact(BaseModel):
    """WhatsApp contact information"""
    profile: WhatsAppProfile
    wa_id: str  # WhatsApp ID (phone number)


class WhatsAppTextMessage(BaseModel):
    """Text message content"""
    body: str  # The actual message text


class WhatsAppMessage(BaseModel):
    """Individual WhatsApp message"""
    from_: str = Field(alias="from")  # Sender's phone number
    id: str  # Message ID
    timestamp: str
    text: Optional[WhatsAppTextMessage] = None
    type: str  # "text", "image", etc.
    from_logical_id: Optional[str] = None  # Additional field from WhatsApp

    class Config:
        extra = "ignore"  # Ignore any additional fields we don't recognize


class WhatsAppMetadata(BaseModel):
    """Metadata about the WhatsApp Business Account"""
    display_phone_number: str
    phone_number_id: str


class WhatsAppValue(BaseModel):
    """Value object containing messages and metadata"""
    messaging_product: str  # Should be "whatsapp"
    metadata: WhatsAppMetadata
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessage]] = None


class WhatsAppChange(BaseModel):
    """Change object in webhook payload"""
    value: WhatsAppValue
    field: str  # Should be "messages"


class WhatsAppEntry(BaseModel):
    """Entry object in webhook payload"""
    id: str  # WhatsApp Business Account ID
    changes: List[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    """
    Complete WhatsApp webhook payload structure
    Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
    """
    object: str  # Should be "whatsapp_business_account"
    entry: List[WhatsAppEntry]


# WhatsApp API Response Models (Outgoing Messages)

class WhatsAppTextRequest(BaseModel):
    """Request to send a text message via WhatsApp API"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str  # Recipient phone number
    type: str = "text"
    text: Dict[str, str]  # {"body": "message content"}


class WhatsAppMessageResponse(BaseModel):
    """Response from WhatsApp API when sending a message"""
    messaging_product: str
    contacts: List[Dict[str, str]]  # [{"input": "phone", "wa_id": "whatsapp_id"}]
    messages: List[Dict[str, str]]  # [{"id": "message_id"}]


# Internal Application Models

class BotRequest(BaseModel):
    """Internal model for processing bot requests"""
    user_id: str  # WhatsApp user ID
    message: str  # User's message text
    message_id: str  # WhatsApp message ID


class BotResponse(BaseModel):
    """Internal model for bot responses"""
    user_id: str
    response: str  # Bot's response text
    success: bool = True
    error: Optional[str] = None


# Health Check Models

class HealthResponse(BaseModel):
    """Health check response"""
    status: str  # "healthy" or "unhealthy"
    database: bool  # Database connection status
    openai: bool  # OpenAI API key present
    whatsapp: bool  # WhatsApp credentials present
    message: str
