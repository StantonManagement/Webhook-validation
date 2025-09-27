"""
Pydantic schemas for Collections Backend API per paul-backend.md specification.
Implements Field aliases for camelCase conversion as required.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, Field


# Update schemas for PATCH endpoints
class TenantUpdate(BaseModel):
    """Schema for PATCH /api/tenants/{id} updates."""
    status: Optional[str] = None
    priority_score: Optional[int] = Field(None, alias="priorityScore")
    language_preference: Optional[str] = Field(None, alias="languagePreference")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class ConversationUpdate(BaseModel):
    """Schema for PATCH /api/conversations/{id} updates."""
    status: Optional[str] = None
    conversation_status: Optional[str] = Field(None, alias="conversationStatus")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class PaymentPlanUpdate(BaseModel):
    """Schema for PATCH /api/payment-plans/{id} updates."""
    status: Optional[str] = None
    weekly_amount: Optional[float] = Field(None, alias="weeklyAmount")
    start_date: Optional[date] = Field(None, alias="startDate")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class EscalationUpdate(BaseModel):
    """Schema for PATCH /api/escalations/{id} updates."""
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    
    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


# Response schemas with Field aliases for camelCase conversion
class TenantResponse(BaseModel):
    """Tenant response model with camelCase field conversion."""
    id: str
    tenant_name: str = Field(alias="tenantName")
    unit_name: str = Field(alias="unitName")
    property_name: str = Field(alias="propertyName")
    amount_owed: str = Field(alias="amountOwed")  # String as per spec
    tenant_portion: Optional[str] = Field(None, alias="tenantPortion")
    days_late: int = Field(alias="daysLate")
    priority_score: int = Field(alias="priorityScore")
    status: str
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    language_preference: str = Field(alias="languagePreference")
    last_contact_date: Optional[datetime] = Field(None, alias="lastContactDate")
    payment_reliability: int = Field(alias="paymentReliability")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat() + 'Z' if dt else None
        }


class MessageResponse(BaseModel):
    """SMS message response model."""
    id: str
    direction: str
    content: str
    timestamp: datetime
    needs_approval: bool = Field(alias="needsApproval")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat() + 'Z' if dt else None
        }


class ConversationResponse(BaseModel):
    """Conversation response model with embedded messages."""
    id: str
    tenant_id: str = Field(alias="tenantId")
    tenant_name: str = Field(alias="tenantName")
    status: str
    language: str
    last_message: Optional[str] = Field(None, alias="lastMessage")
    last_message_at: Optional[datetime] = Field(None, alias="lastMessageAt")
    ai_confidence: float = Field(alias="aiConfidence")
    messages: List[MessageResponse] = []
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat() + 'Z' if dt else None
        }


class PaymentPlanResponse(BaseModel):
    """Payment plan response model."""
    id: str
    tenant_id: str = Field(alias="tenantId")
    tenant_name: str = Field(alias="tenantName")
    total_amount: float = Field(alias="totalAmount")
    weekly_amount: float = Field(alias="weeklyAmount")
    number_of_payments: int = Field(alias="numberOfPayments")
    start_date: str = Field(alias="startDate")  # String as per spec
    status: str
    ai_proposed: bool = Field(alias="aiProposed")
    ai_confidence: float = Field(alias="aiConfidence")
    covers_full_amount: bool = Field(alias="coversFullAmount")
    includes_late_fees: bool = Field(alias="includesLateFees")
    
    class Config:
        populate_by_name = True


class EscalationResponse(BaseModel):
    """Escalation response model."""
    id: str
    conversation_id: str = Field(alias="conversationId")
    escalation_reason: str = Field(alias="escalationReason")
    priority: str
    status: str
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    created_at: datetime = Field(alias="createdAt")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat() + 'Z' if dt else None
        }


class DashboardStatsResponse(BaseModel):
    """Dashboard stats response model."""
    pending: int
    active: int
    approval: int
    escalated: int
    total_tenants: int = Field(alias="totalTenants")
    total_owed: float = Field(alias="totalOwed")
    
    class Config:
        populate_by_name = True