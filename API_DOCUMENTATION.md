# Collections Backend API - Complete Endpoint Documentation

This document provides detailed information about all 11 API endpoints, including request/response formats, error handling, and example curl commands.

## Base URL
- **Local Development**: `http://localhost:8000`
- **Production**: Replace with your deployed API URL

## Authentication
Currently, no authentication is required. All endpoints are publicly accessible.

---

## 1. Tenant Management Endpoints

### GET /api/tenants
Retrieve all tenants in the collections queue.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/tenants" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
[
  {
    "id": "uuid-12345",
    "tenantName": "John Smith",
    "unitName": "101",
    "propertyName": "Sunset Apartments",
    "amountOwed": "1500.00",
    "tenantPortion": "500.00",
    "daysLate": 15,
    "priorityScore": 85,
    "status": "pending",
    "phoneNumber": "+1234567890",
    "languagePreference": "english",
    "lastContactDate": "2025-01-15T10:00:00Z",
    "paymentReliability": 7
  }
]
```

**Error Responses:**
- `500 Internal Server Error`: Database connection issues

---

### GET /api/tenants/{id}
Retrieve specific tenant details by ID.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/tenants/uuid-12345" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "id": "uuid-12345",
  "tenantName": "John Smith",
  "unitName": "101",
  "propertyName": "Sunset Apartments",
  "amountOwed": "1500.00",
  "tenantPortion": "500.00",
  "daysLate": 15,
  "priorityScore": 85,
  "status": "pending",
  "phoneNumber": "+1234567890",
  "languagePreference": "english",
  "lastContactDate": "2025-01-15T10:00:00Z",
  "paymentReliability": 7
}
```

**Error Responses:**
- `404 Not Found`: Tenant ID not found
- `500 Internal Server Error`: Database connection issues

---

### PATCH /api/tenants/{id}
Update tenant information (status, priority score, language preference).

**Request:**
```bash
curl -X PATCH "http://localhost:8000/api/tenants/uuid-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "priorityScore": 90,
    "languagePreference": "spanish"
  }'
```

**Request Body Schema:**
```json
{
  "status": "string (optional)",           // pending, active, resolved, escalated
  "priorityScore": "integer (optional)",   // 1-100
  "languagePreference": "string (optional)" // english, spanish, etc.
}
```

**Response (200 OK):**
```json
{
  "id": "uuid-12345",
  "tenantName": "John Smith",
  "unitName": "101",
  "propertyName": "Sunset Apartments",
  "amountOwed": "1500.00",
  "tenantPortion": "500.00",
  "daysLate": 15,
  "priorityScore": 90,
  "status": "active",
  "phoneNumber": "+1234567890",
  "languagePreference": "spanish",
  "lastContactDate": "2025-01-15T10:00:00Z",
  "paymentReliability": 7
}
```

**Error Responses:**
- `404 Not Found`: Tenant ID not found
- `422 Unprocessable Entity`: Invalid request data
- `500 Internal Server Error`: Database update failed

---

## 2. Conversation Management Endpoints

### GET /api/conversations
Retrieve all SMS conversations with message history.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/conversations" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
[
  {
    "id": "conv-uuid-1",
    "tenantId": "12345",
    "tenantName": "John Smith",
    "status": "active",
    "language": "english",
    "lastMessage": "I can pay $200 this week",
    "lastMessageAt": "2025-01-15T14:30:00Z",
    "aiConfidence": 0.85,
    "messages": [
      {
        "id": "msg-uuid-1",
        "direction": "outbound",
        "content": "Hello John, this is regarding your outstanding balance of $1500. Can we discuss a payment plan?",
        "timestamp": "2025-01-15T10:00:00Z",
        "needsApproval": false
      },
      {
        "id": "msg-uuid-2",
        "direction": "inbound",
        "content": "I can pay $200 this week",
        "timestamp": "2025-01-15T14:30:00Z",
        "needsApproval": false
      }
    ]
  }
]
```

**Error Responses:**
- `500 Internal Server Error`: Database connection issues

---

### GET /api/conversations/tenant/{tenant_id}
Retrieve conversations for a specific tenant.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/conversations/tenant/12345" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
Same format as GET /api/conversations, but filtered for the specific tenant.

**Error Responses:**
- `404 Not Found`: No conversations found for tenant
- `500 Internal Server Error`: Database connection issues

---

### PATCH /api/conversations/{id}
Update conversation status or properties.

**Request:**
```bash
curl -X PATCH "http://localhost:8000/api/conversations/conv-uuid-1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "language": "spanish"
  }'
```

**Request Body Schema:**
```json
{
  "status": "string (optional)",    // active, paused, resolved, escalated
  "language": "string (optional)"   // english, spanish, etc.
}
```

**Response (200 OK):**
Updated conversation object with same format as GET response.

**Error Responses:**
- `404 Not Found`: Conversation ID not found
- `422 Unprocessable Entity`: Invalid request data
- `500 Internal Server Error`: Database update failed

---

## 3. Payment Plan Endpoints

### GET /api/payment-plans
Retrieve all payment plans.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/payment-plans" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
[
  {
    "id": "plan-uuid-1",
    "tenantId": "12345",
    "tenantName": "John Smith",
    "totalAmount": 1500.00,
    "weeklyAmount": 200.00,
    "numberOfPayments": 8,
    "startDate": "2025-01-20",
    "status": "pending",
    "aiProposed": true,
    "aiConfidence": 0.92,
    "coversFullAmount": true,
    "includesLateFees": true
  }
]
```

**Error Responses:**
- `500 Internal Server Error`: Database connection issues

---

### PATCH /api/payment-plans/{id}
Update payment plan status or details.

**Request:**
```bash
curl -X PATCH "http://localhost:8000/api/payment-plans/plan-uuid-1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "weeklyAmount": 250.00,
    "numberOfPayments": 6
  }'
```

**Request Body Schema:**
```json
{
  "status": "string (optional)",           // pending, approved, active, completed, cancelled
  "weeklyAmount": "number (optional)",     // Weekly payment amount
  "numberOfPayments": "integer (optional)", // Total number of payments
  "startDate": "string (optional)"         // ISO date string
}
```

**Response (200 OK):**
Updated payment plan object with same format as GET response.

**Error Responses:**
- `404 Not Found`: Payment plan ID not found
- `422 Unprocessable Entity`: Invalid request data
- `500 Internal Server Error`: Database update failed

---

## 4. Escalation Management Endpoints

### GET /api/escalations
Retrieve all escalated items.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/escalations" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
[
  {
    "id": "esc-uuid-1",
    "conversationId": "conv-uuid-1",
    "tenantName": "John Smith",
    "reason": "Payment plan rejected multiple times",
    "priority": "high",
    "status": "pending",
    "assignedTo": "Manager Smith",
    "createdAt": "2025-01-15T16:00:00Z",
    "daysOpen": 2
  }
]
```

**Error Responses:**
- `500 Internal Server Error`: Database connection issues

---

### PATCH /api/escalations/{id}
Update escalation status or assignment.

**Request:**
```bash
curl -X PATCH "http://localhost:8000/api/escalations/esc-uuid-1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "assignedTo": "Senior Manager Jones",
    "priority": "urgent"
  }'
```

**Request Body Schema:**
```json
{
  "status": "string (optional)",      // pending, in_progress, resolved, escalated_further
  "assignedTo": "string (optional)",  // Staff member name
  "priority": "string (optional)"     // low, medium, high, urgent
}
```

**Response (200 OK):**
Updated escalation object with same format as GET response.

**Error Responses:**
- `404 Not Found`: Escalation ID not found
- `422 Unprocessable Entity`: Invalid request data
- `500 Internal Server Error`: Database update failed

---

## 5. Dashboard Statistics Endpoint

### GET /api/dashboard/stats
Retrieve dashboard statistics and counts.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/dashboard/stats" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "pending": 45,
  "active": 23,
  "approval": 12,
  "escalated": 5,
  "totalTenants": 85,
  "totalOwed": 125000.50
}
```

**Field Descriptions:**
- `pending`: Tenants awaiting initial contact
- `active`: Tenants with ongoing conversations
- `approval`: Items requiring manager approval
- `escalated`: Items escalated for manual intervention
- `totalTenants`: Total number of tenants in collections
- `totalOwed`: Sum of all outstanding amounts (as number)

**Error Responses:**
- `500 Internal Server Error`: Database connection issues

---

## 6. System Status Endpoints

### GET /
API information and status.

**Request:**
```bash
curl -X GET "http://localhost:8000/" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "service": "Collections Backend API",
  "version": "1.0.0",
  "status": "operational",
  "endpoints": [
    "GET /api/tenants",
    "GET /api/tenants/{id}",
    "PATCH /api/tenants/{id}",
    "GET /api/conversations",
    "GET /api/conversations/tenant/{tenant_id}",
    "PATCH /api/conversations/{id}",
    "GET /api/payment-plans",
    "PATCH /api/payment-plans/{id}",
    "GET /api/escalations",
    "PATCH /api/escalations/{id}",
    "GET /api/dashboard/stats"
  ]
}
```

---

### GET /health
Health check endpoint for monitoring.

**Request:**
```bash
curl -X GET "http://localhost:8000/health" \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "core_requirements_met": true,
  "total_endpoints": 11,
  "specification_compliant": true
}
```

---

## Common Error Responses

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity (Validation Error)
```json
{
  "detail": [
    {
      "loc": ["body", "status"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred"
}
```

---

## Rate Limiting
Currently, no rate limiting is implemented. All endpoints can be called without restrictions.

## CORS Policy
The API supports CORS for frontend access. Ensure your frontend URL is configured in the `FRONTEND_URL` environment variable.

## Testing Examples

### Complete Workflow Test
```bash
# 1. Get all tenants
curl -X GET "http://localhost:8000/api/tenants"

# 2. Get specific tenant
curl -X GET "http://localhost:8000/api/tenants/uuid-12345"

# 3. Update tenant status
curl -X PATCH "http://localhost:8000/api/tenants/uuid-12345" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'

# 4. Get conversations for tenant
curl -X GET "http://localhost:8000/api/conversations/tenant/12345"

# 5. Check dashboard stats
curl -X GET "http://localhost:8000/api/dashboard/stats"

# 6. Health check
curl -X GET "http://localhost:8000/health"
```

### Error Testing
```bash
# Test 404 - invalid tenant ID
curl -X GET "http://localhost:8000/api/tenants/invalid-uuid"

# Test validation error - invalid PATCH data
curl -X PATCH "http://localhost:8000/api/tenants/uuid-12345" \
  -H "Content-Type: application/json" \
  -d '{"invalidField": "value"}'
```

---

## Interactive API Documentation

For interactive testing and detailed schema information:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces provide:
- Interactive endpoint testing
- Complete request/response schemas
- Authentication details (when implemented)
- Example requests and responses