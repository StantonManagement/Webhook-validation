"""
Unit tests for webhook validation endpoints.
Simplified tests that match the actual model structure and conftest.py fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class TestPaymentWebhook:
    """Test cases for payment webhook endpoint."""
    
    def test_valid_payment_webhook(self, sample_payment_webhook):
        """Test payment webhook with valid payload from conftest fixture."""
        response = client.post("/webhook/payment", json=sample_payment_webhook)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Payment webhook validated successfully" in data["message"]
        assert data["webhook_type"] == "payment"
    
    def test_invalid_payment_webhook(self, invalid_payment_webhook):
        """Test payment webhook with invalid payload from conftest fixture."""
        response = client.post("/webhook/payment", json=invalid_payment_webhook)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Validation failed" in data["message"]
        assert "errors" in data
    
    def test_missing_payment_fields(self):
        """Test payment webhook with missing required fields."""
        payload = {"amount": "29.99"} 
        
        response = client.post("/webhook/payment", json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


class TestSmsWebhook:
    """Test cases for SMS webhook endpoint."""
    
    def test_valid_sms_webhook(self, sample_sms_webhook):
        """Test SMS webhook with valid payload from conftest fixture."""
        response = client.post("/webhook/sms", json=sample_sms_webhook)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "SMS webhook validated successfully" in data["message"]
        assert data["webhook_type"] == "sms"
    
    def test_invalid_sms_webhook(self, invalid_sms_webhook):
        """Test SMS webhook with invalid payload from conftest fixture."""
        response = client.post("/webhook/sms", json=invalid_sms_webhook)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Validation failed" in data["message"]
    
    def test_missing_sms_fields(self):
        """Test SMS webhook with missing required fields."""
        payload = {"MessageSid": "test"}  
        
        response = client.post("/webhook/sms", json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


class TestEmailWebhook:
    """Test cases for email webhook endpoint."""
    
    def test_valid_email_webhook(self, sample_email_webhook):
        """Test email webhook with valid payload from conftest fixture."""
        response = client.post("/webhook/email", json=sample_email_webhook)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Email webhook validated successfully" in data["message"]
        assert data["webhook_type"] == "email"
    
    def test_invalid_email_webhook(self, invalid_email_webhook):
        """Test email webhook with invalid payload from conftest fixture."""
        response = client.post("/webhook/email", json=invalid_email_webhook)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Validation failed" in data["message"]
    
    def test_missing_email_fields(self):
        """Test email webhook with missing required fields."""
        payload = {"email": "test@example.com"} 
        
        response = client.post("/webhook/email", json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


class TestServiceEndpoints:
    """Test cases for service endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns service information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Webhook Validator Service"
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert data["endpoints"]["payment"] == "/webhook/payment"
        assert data["endpoints"]["sms"] == "/webhook/sms"
        assert data["endpoints"]["email"] == "/webhook/email"
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "webhook-validator-service"


def test_all_webhooks_integration(sample_payment_webhook, sample_sms_webhook, sample_email_webhook):
    """Integration test for all webhook endpoints using conftest fixtures."""
    # Test payment webhook
    response = client.post("/webhook/payment", json=sample_payment_webhook)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Test SMS webhook
    response = client.post("/webhook/sms", json=sample_sms_webhook)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Test email webhook
    response = client.post("/webhook/email", json=sample_email_webhook)
    assert response.status_code == 200
    assert response.json()["success"] is True