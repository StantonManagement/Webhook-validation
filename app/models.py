"""
Pydantic models for webhook validation.
Simplified implementation that matches test specification requirements.
"""

from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class PaymentStatus(str, Enum):
    """Payment status values."""
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"
    CANCELED = "canceled"


class SmsStatus(str, Enum):
    """SMS status values."""
    DELIVERED = "delivered"
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"


class EmailEventType(str, Enum):
    """Email event types."""
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCE = "bounce"
    DROPPED = "dropped"


class PaymentWebhook(BaseModel):
    """Payment webhook payload model - simplified for test requirements."""
    id: str = Field(..., description="Payment intent ID")
    object: str = Field(default="payment_intent", description="Object type")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    amount_received: Decimal = Field(..., ge=0, description="Amount received")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO currency code")
    status: PaymentStatus = Field(..., description="Payment status")
    created: datetime = Field(..., description="Payment creation timestamp")
    description: Optional[str] = Field(None, description="Payment description")

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        """Ensure currency is uppercase."""
        return v.upper()

    @field_validator('amount', 'amount_received')
    @classmethod
    def validate_amounts(cls, v):
        """Ensure amounts are non-negative."""
        if v < 0:
            raise ValueError('Amount must be non-negative')
        return v


class SmsWebhook(BaseModel):
    """SMS webhook payload model - simplified for test requirements."""
    message_sid: str = Field(..., alias="MessageSid", min_length=1, description="Unique message identifier")
    account_sid: str = Field(..., alias="AccountSid", min_length=1, description="Account identifier")
    from_: str = Field(..., alias="From", min_length=1, description="Sender phone number")
    to: str = Field(..., alias="To", min_length=1, description="Recipient phone number")
    body: Optional[str] = Field(None, alias="Body", description="Message body")
    num_media: int = Field(default=0, alias="NumMedia", ge=0, description="Number of media attachments")
    num_segments: int = Field(default=1, alias="NumSegments", ge=1, description="Number of message segments")
    message_status: SmsStatus = Field(..., alias="MessageStatus", description="SMS delivery status")
    date_created: Optional[datetime] = Field(None, alias="DateCreated", description="Message creation timestamp")

    model_config = ConfigDict(populate_by_name=True)


class EmailWebhook(BaseModel):
    """Email webhook payload model - simplified for test requirements."""
    email: EmailStr = Field(..., description="Recipient email address")
    timestamp: int = Field(..., description="Event timestamp (Unix timestamp)")
    event: EmailEventType = Field(..., description="Email event type")
    sg_event_id: str = Field(..., min_length=1, description="SendGrid event identifier")
    sg_message_id: str = Field(..., min_length=1, description="SendGrid message identifier")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid."""
        if v <= 0:
            raise ValueError('Timestamp must be positive')
        return v


class WebhookResponse(BaseModel):
    """Standard response model for webhook endpoints."""
    success: bool = Field(..., description="Whether the webhook was processed successfully")
    message: str = Field(..., description="Response message")
    event_id: Optional[str] = Field(None, description="Event identifier for logging")
    webhook_type: Optional[str] = Field(None, description="Type of webhook processed")