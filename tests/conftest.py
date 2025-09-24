"""
Pytest configuration and fixtures for the webhook validator service.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Generator, Dict, Any

from main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_payment_webhook() -> Dict[str, Any]:
    """Sample valid payment webhook payload - simplified for basic testing."""
    return {
        "id": "pi_test_1234567890",
        "object": "payment_intent",
        "amount": "29.99",
        "amount_received": "29.99",
        "currency": "USD",
        "status": "succeeded",
        "created": "2023-12-01T12:00:00Z",
        "description": "Test payment"
    }


@pytest.fixture
def sample_sms_webhook() -> Dict[str, Any]:
    """Sample valid SMS webhook payload - simplified for basic testing."""
    return {
        "MessageSid": "SM_test_1234567890abcdef",
        "AccountSid": "AC_test_1234567890abcdef",
        "From": "+1234567890",
        "To": "+0987654321",
        "Body": "Test SMS message",
        "NumMedia": "0",
        "NumSegments": "1",
        "MessageStatus": "delivered",
        "DateCreated": "2023-12-01T12:00:00Z"
    }


@pytest.fixture
def sample_email_webhook() -> Dict[str, Any]:
    """Sample valid email webhook payload - simplified for basic testing."""
    return {
        "email": "test@example.com",
        "timestamp": 1701432000,
        "event": "delivered",
        "sg_event_id": "sg_test_123456789",
        "sg_message_id": "test.123.456.789.abcdef"
    }


@pytest.fixture
def invalid_payment_webhook() -> Dict[str, Any]:
    """Sample invalid payment webhook payload for testing validation."""
    return {
        "id": "pi_invalid",
        "amount": "invalid_amount",  # Should be numeric
        "currency": "INVALID_CURRENCY",  # Too long
        "status": "invalid_status"  # Invalid status
    }


@pytest.fixture
def invalid_sms_webhook() -> Dict[str, Any]:
    """Sample invalid SMS webhook payload for testing validation."""
    return {
        "MessageSid": "",  # Empty required field
        "AccountSid": "AC_test",
        "From": "+123",
        "To": "+456",
        "MessageStatus": "invalid_status",  # Invalid status
        "NumMedia": "-1"  # Should be non-negative
    }


@pytest.fixture
def invalid_email_webhook() -> Dict[str, Any]:
    """Sample invalid email webhook payload for testing validation."""
    return {
        "email": "invalid-email",  # Invalid email format
        "timestamp": -1,  # Invalid timestamp
        "event": "invalid_event",  # Invalid event type
        "sg_event_id": "",  # Empty required field
        "sg_message_id": ""  # Empty required field
    }


@pytest.fixture
def webhook_headers() -> Dict[str, str]:
    """Standard headers for webhook requests."""
    return {
        "Content-Type": "application/json",
        "User-Agent": "TestWebhookClient/1.0"
    }