"""
FastAPI Main Application
Handles webhook endpoints for WhatsApp integration
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse
import logging
from typing import Dict, Any

from app.config import config
from app.models import HealthResponse
from app.whatsapp import (
    whatsapp_client,
    parse_webhook_payload,
    send_error_message,
    verify_webhook_signature
)
from app.chat_service import ChatService
from app.utils import setup_logging

# Setup logging
logger = setup_logging(config.LOG_LEVEL)

# Initialize FastAPI app
app = FastAPI(
    title="SaladBot API",
    description="WhatsApp Bot for Salad & Deli Menu Queries",
    version="1.0.0"
)

# Initialize chat service (singleton for the application)
chat_service = ChatService()


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "SaladBot API",
        "version": "1.0.0",
        "status": "running",
        "description": "WhatsApp bot for salad and deli menu queries"
    }


@app.get("/health")
async def health_check() -> HealthResponse:
    """
    Health check endpoint
    Validates that all required services are available
    """
    # Check database connection
    database_ok = bool(config.SUPABASE_URL and config.SUPABASE_KEY)

    # Check OpenAI API key
    openai_ok = bool(config.OPENAI_API_KEY)

    # Check WhatsApp credentials
    whatsapp_ok = bool(
        config.WHATSAPP_ACCESS_TOKEN and
        config.WHATSAPP_PHONE_NUMBER_ID and
        config.WHATSAPP_VERIFY_TOKEN
    )

    # Overall status
    all_ok = database_ok and openai_ok and whatsapp_ok

    status = "healthy" if all_ok else "unhealthy"
    message = "All systems operational" if all_ok else "Some systems are missing configuration"

    return HealthResponse(
        status=status,
        database=database_ok,
        openai=openai_ok,
        whatsapp=whatsapp_ok,
        message=message
    )


@app.get("/webhook")
async def webhook_verify(request: Request):
    """
    Webhook verification endpoint (GET)
    WhatsApp sends a verification request when you configure the webhook URL

    Expected query parameters:
    - hub.mode: Should be "subscribe"
    - hub.verify_token: Should match WHATSAPP_VERIFY_TOKEN
    - hub.challenge: Random string to echo back
    """
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info(f"Webhook verification request received: mode={mode}, token={'***' if token else None}")

    # Verify the mode and token
    if mode == "subscribe" and token == config.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        # Respond with the challenge token
        return PlainTextResponse(content=challenge)
    else:
        logger.error("Webhook verification failed: Invalid token or mode")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Webhook message handler (POST)
    Receives incoming WhatsApp messages and responds with bot replies

    Flow:
    1. Verify webhook signature (security)
    2. Parse incoming message
    3. Process message with agent
    4. Send response back to user
    """
    try:
        # Get raw body for signature verification
        body = await request.body()

        # Verify webhook signature (optional in development)
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_webhook_signature(body, signature):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse JSON payload
        payload = await request.json()

        logger.info("Webhook POST request received")
        logger.debug(f"Payload: {payload}")

        # Parse webhook payload to extract message
        bot_request = parse_webhook_payload(payload)

        if not bot_request:
            # No text message found (might be status update, media, etc.)
            logger.info("No processable message in webhook payload")
            return {"status": "ok", "message": "No text message to process"}

        # Extract message details
        user_id = bot_request.user_id
        user_message = bot_request.message
        message_id = bot_request.message_id

        logger.info(f"Processing message from {user_id}: {user_message[:100]}...")

        # Process message with chat service (with conversation history)
        try:
            bot_response = await chat_service.process_user_message(
                user_message=user_message,
                user_id=user_id,  # Track history per user
                reset_history=False  # Keep conversation context
            )

            logger.info(f"Chat service response generated: {bot_response[:100]}...")

            # Send response back to user
            success = whatsapp_client.send_text_message(
                to=user_id,
                message=bot_response
            )

            if success:
                # Optionally mark message as read
                whatsapp_client.mark_message_as_read(message_id)
                logger.info(f"Response sent successfully to {user_id}")
            else:
                logger.error(f"Failed to send response to {user_id}")
                # Don't send error message to avoid infinite loop

            return {"status": "ok", "message": "Message processed"}

        except Exception as agent_error:
            logger.error(f"Agent processing error: {str(agent_error)}")
            # Send user-friendly error message
            send_error_message(user_id, "general")
            return {"status": "error", "message": "Agent processing failed"}

    except Exception as e:
        logger.error(f"Webhook handler error: {str(e)}")
        # Return 200 to prevent WhatsApp from retrying
        return {"status": "error", "message": str(e)}


@app.post("/test-message")
async def test_message(request: Request):
    """
    Test endpoint for sending messages directly (development only)

    Request body:
    {
        "to": "recipient_phone_number",
        "message": "test message"
    }
    """
    try:
        data = await request.json()
        to = data.get("to")
        message = data.get("message")

        if not to or not message:
            raise HTTPException(status_code=400, detail="Missing 'to' or 'message' field")

        # Process message with chat service
        bot_response = await chat_service.process_user_message(message, reset_history=True)

        # Send response
        success = whatsapp_client.send_text_message(to, bot_response)

        if success:
            return {
                "status": "success",
                "message": "Test message sent",
                "bot_response": bot_response
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")

    except Exception as e:
        logger.error(f"Test message error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info("  SALADBOT API STARTING")
    logger.info("=" * 60)

    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed!")
    else:
        logger.info("Core configuration validated successfully")

    if not config.validate_whatsapp():
        logger.warning("WhatsApp configuration incomplete (optional for development)")
    else:
        logger.info("WhatsApp configuration validated successfully")

    logger.info(f"Chat service initialized with model: {chat_service.model}")
    logger.info("API ready to receive requests")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("SaladBot API shutting down...")


if __name__ == "__main__":
    import uvicorn

    # Run server (development mode)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.SERVER_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
