"""
Webhook routes for payment, SMS, and email validation.
Handles POST endpoints with proper validation and logging.
"""

import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from .models import (
    PaymentWebhook,
    SmsWebhook,
    EmailWebhook,
    WebhookResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


def log_webhook_event(event_type: str, event_id: str, timestamp: datetime = None):
    """
    Log webhook events without exposing sensitive data.
    
    Args:
        event_type: Type of webhook (payment, sms, email)
        event_id: Unique identifier for the event
        timestamp: Event timestamp (defaults to current time)
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    logger.info(f"Webhook received - Type: {event_type}, Event ID: {event_id}, Timestamp: {timestamp.isoformat()}")


@router.post("/payment", response_model=WebhookResponse, status_code=200)
async def validate_payment_webhook(payload: PaymentWebhook):
    """
    Validate Stripe-style payment webhook.
    
    Expects payload with:
    - id: Payment intent ID
    - amount: Payment amount in smallest currency unit (cents)
    - currency: ISO currency code (3 letters)
    - status: Payment status (succeeded, failed, pending, etc.)
    - customer: Optional customer information
    - payment_method: Optional payment method details
    - created: Payment creation timestamp
    
    Returns confirmation with event ID for successful validation.
    """
    try:
        # Use the payment intent ID as the event ID
        event_id = payload.id
        
        # Log the webhook event (without sensitive data)
        log_webhook_event("payment", event_id, payload.created)
        
        return WebhookResponse(
            success=True,
            message=f"Payment webhook validated successfully. ID: {payload.id}, Amount: {payload.amount} {payload.currency}, Status: {payload.status}",
            event_id=event_id,
            processed_at=datetime.now(timezone.utc),
            webhook_type="payment"
        )
        
    except ValidationError as e:
        logger.warning(f"Payment webhook validation failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment webhook payload: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing payment webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing payment webhook"
        )


@router.post("/sms", response_model=WebhookResponse, status_code=200)
async def validate_sms_webhook(payload: SmsWebhook):
    """
    Validate Twilio-style SMS webhook.
    
    Expects payload with:
    - MessageSid: Unique message identifier
    - From: Sender phone number
    - To: Recipient phone number
    - MessageStatus: SMS delivery status
    - DateCreated: Message creation timestamp
    
    Returns confirmation with event ID for successful validation.
    """
    try:
        # Use the message SID as the event ID
        event_id = payload.message_sid
        
        # Log the webhook event (without sensitive data)
        log_webhook_event("sms", event_id, payload.date_created)
        
        return WebhookResponse(
            success=True,
            message=f"SMS webhook validated successfully. Message SID: {payload.message_sid}, Status: {payload.message_status}",
            event_id=event_id,
            processed_at=datetime.now(timezone.utc),
            webhook_type="sms"
        )
        
    except ValidationError as e:
        logger.warning(f"SMS webhook validation failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid SMS webhook payload: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing SMS webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing SMS webhook"
        )


@router.post("/email", response_model=WebhookResponse, status_code=200)
async def validate_email_webhook(payload: EmailWebhook):
    """
    Validate SendGrid-style email webhook.
    
    Expects payload with:
    - email: Recipient email address (EmailStr format)
    - event: Email event type (processed, delivered, opened, clicked, etc.)
    - sg_event_id: SendGrid event identifier
    - timestamp: Event timestamp (Unix timestamp)
    - reason: Optional reason for bounce/drop events
    
    Returns confirmation with event ID for successful validation.
    """
    try:
        # Use the SendGrid event ID as the event ID
        event_id = payload.sg_event_id
        
        # Convert Unix timestamp to datetime for logging
        event_datetime = datetime.fromtimestamp(payload.timestamp)
        log_webhook_event("email", event_id, event_datetime)
        
        # Simple success message for email webhook
        message = f"Email webhook validated successfully. Event: {payload.event}, SG Event ID: {payload.sg_event_id}"
        
        return WebhookResponse(
            success=True,
            message=message,
            event_id=event_id,
            processed_at=datetime.now(timezone.utc),
            webhook_type="email"
        )
        
    except ValidationError as e:
        logger.warning(f"Email webhook validation failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid email webhook payload: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing email webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing email webhook"
        )