# Backend API Integration Service - Project Specification

## Project Overview
Build a FastAPI service that replaces the mock storage.ts in our React dashboard with real data from Supabase and existing microservices. This service acts as the bridge between the frontend dashboard and our backend systems.

## Payment & Timeline
- **Payment**: $125 flat fee
- **Timeline**: 48 hours from start confirmation
- **Speed Bonus**: Additional $25 if delivered within 48 hours with tests passing
- **Total Potential**: $150

## Business Context
Our React dashboard currently uses mock data from storage.ts. Your API will:
1. Connect to Supabase for collections data
2. Integrate with Kurt's Collections Monitor for tenant information
3. Serve real-time data to the dashboard
4. Maintain the exact JSON structure the dashboard expects
5. Enable the collections team to see real delinquent tenants and conversations

## Core Requirements

### 1. Replace These Express Routes with FastAPI

You need to create FastAPI endpoints that exactly match what the dashboard expects:

```python
# Tenants endpoints
GET /api/tenants
GET /api/tenants/{id}
PATCH /api/tenants/{id}

# Conversations endpoints  
GET /api/conversations
GET /api/conversations/tenant/{tenant_id}
PATCH /api/conversations/{id}

# Payment Plans endpoints
GET /api/payment-plans
PATCH /api/payment-plans/{id}

# Escalations endpoints
GET /api/escalations
PATCH /api/escalations/{id}

# Dashboard stats
GET /api/dashboard/stats
```

### 2. Data Sources

**From Supabase directly:**
```sql
-- Collections Queue (main tenant list)
collections_queue (
  id uuid,
  tenant_id bigint,
  tenant_name text,
  unit_name text, 
  property_name text,
  amount_owed numeric,
  tenant_portion numeric,
  days_late integer,
  priority_score integer,
  status text,
  language_preference text,
  created_at timestamp
)

-- SMS Conversations
sms_conversations (
  id uuid,
  collections_queue_id uuid,
  tenant_profile_id uuid,
  phone_number text,
  tenant_name text,
  conversation_status text,
  language_detected text,  -- Note: field is language_detected, not language
  ai_confidence_score numeric,
  last_message_at timestamp
)

-- SMS Messages (for conversation history)
sms_messages (
  id uuid,
  conversation_id uuid,  -- FK to sms_conversations
  direction text,        -- 'inbound' or 'outbound'
  message_content text,
  twilio_sid text,
  delivery_status text,
  created_at timestamp
)

-- Payment Plans
payment_plans (
  id uuid,
  collections_queue_id uuid,
  tenant_id bigint,  -- Note: tenant_id, not tenant_profile_id
  total_amount numeric,
  weekly_amount numeric,
  number_of_payments integer,
  start_date date,
  status text,
  ai_proposed boolean,
  ai_confidence_score numeric
)

-- Escalated Items
escalated_items (
  id uuid,
  conversation_id uuid,
  escalation_reason text,
  priority text,
  status text,
  assigned_to text,
  created_at timestamp
)

-- Tenant Profiles (for reliability scores)
tenant_profiles (
  tenant_id bigint,
  phone_numbers jsonb,  -- Array of phone objects like [{number: "+1234567890", status: "active"}]
  payment_reliability_score integer,
  failed_payment_plans integer,
  successful_payment_plans integer,
  language_preference text
)
```

**From Kurt's Collections Monitor API:**
```python
# For additional tenant details (fallback if not in tenant_profiles)
GET http://localhost:8001/monitor/tenant/{tenant_id}
# Returns payment history, reliability score, etc.
```

### 3. Expected JSON Response Formats

**GET /api/tenants**
```json
[
  {
    "id": "uuid",
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

**GET /api/conversations**
```json
[
  {
    "id": "uuid",
    "tenantId": "12345",
    "tenantName": "John Smith",
    "status": "active",
    "language": "english",
    "lastMessage": "I can pay $200 this week",
    "lastMessageAt": "2025-01-15T14:30:00Z",
    "aiConfidence": 0.85,
    "messages": [
      {
        "id": "msg-id",
        "direction": "inbound",
        "content": "I can pay $200 this week",
        "timestamp": "2025-01-15T14:30:00Z",
        "needsApproval": false
      }
    ]
  }
]
```

**Important Note:** The messages array needs to be fetched from the `sms_messages` table using the conversation_id as the foreign key.

**GET /api/payment-plans**
```json
[
  {
    "id": "uuid",
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

**GET /api/dashboard/stats**
```json
{
  "pending": 45,
  "active": 23,
  "approval": 12,
  "escalated": 5,
  "totalTenants": 78,
  "totalOwed": 125000.50
}
```

### 4. Technical Implementation

**Project Structure:**
```
backend-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── routers/
│   │   ├── tenants.py
│   │   ├── conversations.py
│   │   ├── payment_plans.py
│   │   ├── escalations.py
│   │   └── dashboard.py
│   ├── services/
│   │   ├── supabase_service.py
│   │   └── monitor_service.py
│   └── schemas.py
├── tests/
│   └── test_api.py
├── requirements.txt
├── .env.example
└── README.md
```

**Key Technical Requirements:**
- Use FastAPI with async/await
- Pydantic for request/response validation
- httpx for calling Kurt's Collections Monitor
- Proper error handling (404s, 500s, etc.)
- CORS enabled for dashboard access
- Connection pooling for Supabase

### 5. Data Transformation

The dashboard uses camelCase, but Supabase uses snake_case. You need to transform:

```python
# From Supabase (snake_case)
tenant_name -> tenantName
amount_owed -> amountOwed
days_late -> daysLate
priority_score -> priorityScore
payment_reliability_score -> paymentReliability
language_detected -> language  # Note the field name difference
conversation_status -> status

# Use Pydantic alias for automatic conversion
class TenantResponse(BaseModel):
    id: str
    tenant_name: str = Field(alias="tenantName")
    amount_owed: Decimal = Field(alias="amountOwed")
    # etc.
    
    class Config:
        populate_by_name = True
        json_encoders = {
            Decimal: str
        }
```

### 6. Integration Points

**With Collections Monitor:**
```python
async def get_tenant_details(tenant_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8001/monitor/tenant/{tenant_id}"
        )
        if response.status_code == 200:
            return response.json()
        return None
```

**With Supabase:**
```python
from supabase import create_client, Client

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Example: Get tenant with profile data
def get_tenant_with_profile(tenant_id: int):
    # Get from collections_queue
    queue_result = supabase.table('collections_queue')\
        .select("*")\
        .eq('tenant_id', tenant_id)\
        .execute()
    
    # Get profile for reliability score
    profile_result = supabase.table('tenant_profiles')\
        .select("*")\
        .eq('tenant_id', tenant_id)\
        .execute()
    
    # Combine data
    tenant_data = queue_result.data[0] if queue_result.data else {}
    profile_data = profile_result.data[0] if profile_result.data else {}
    
    # Extract phone number from JSONB
    phone_numbers = profile_data.get('phone_numbers', [])
    primary_phone = phone_numbers[0]['number'] if phone_numbers else None
    
    return {
        **tenant_data,
        'phone_number': primary_phone,
        'payment_reliability_score': profile_data.get('payment_reliability_score', 5)
    }

# Example: Get conversation with messages
def get_conversation_with_messages(conversation_id: str):
    # Get conversation
    conv_result = supabase.table('sms_conversations')\
        .select("*")\
        .eq('id', conversation_id)\
        .execute()
    
    # Get messages for this conversation
    messages_result = supabase.table('sms_messages')\
        .select("*")\
        .eq('conversation_id', conversation_id)\
        .order('created_at')\
        .execute()
    
    conversation = conv_result.data[0] if conv_result.data else {}
    conversation['messages'] = messages_result.data
    
    return conversation
```

### 7. PATCH Endpoints

For status updates from the dashboard:

```python
@router.patch("/api/tenants/{id}")
async def update_tenant(id: str, update: TenantUpdate):
    # Update collections_queue table
    result = supabase.table('collections_queue')\
        .update(update.dict(exclude_unset=True))\
        .eq('id', id)\
        .execute()
    
    return transform_to_camel_case(result.data[0])

class TenantUpdate(BaseModel):
    status: Optional[str] = None
    priority_score: Optional[int] = None
    language_preference: Optional[str] = None
```

### 8. Special Considerations

**Phone Number Handling:**
- Phone numbers are stored in `tenant_profiles.phone_numbers` as JSONB array
- Format: `[{"number": "+1234567890", "status": "active", "added_date": "2025-01-01"}]`
- Extract the first active number for the dashboard's phoneNumber field

**Reliability Score:**
- Primary source: `tenant_profiles.payment_reliability_score`
- Fallback: Call Kurt's Collections Monitor API if not in tenant_profiles
- Default: 5 if not found anywhere

**Language Preference:**
- Check `tenant_profiles.language_preference` first
- Then `collections_queue.language_preference`
- Then `sms_conversations.language_detected`
- Default: "english"

## Environment Variables

```env
# Supabase
SUPABASE_URL=https://[project].supabase.co
SUPABASE_KEY=[anon-key]

# Collections Monitor
MONITOR_API_URL=http://localhost:8001

# CORS
FRONTEND_URL=http://localhost:3000
```

## Testing Requirements

1. **Unit Tests**
   - Test data transformation (snake_case to camelCase)
   - Test error handling
   - Test phone number extraction from JSONB
   - Test integration with Collections Monitor

2. **Integration Tests**
   - Test all endpoints return correct format
   - Test PATCH operations update database
   - Test stats calculation
   - Test conversation messages fetching

3. **Test Data**
   - Include script to populate test data
   - Minimum 10 test tenants with various statuses
   - Create sample conversations with messages
   - Create tenant profiles with phone numbers

## Success Criteria

- [ ] All 10 endpoints working with correct JSON format
- [ ] Dashboard can display real data (no more mocks)
- [ ] Priority scores calculated if missing
- [ ] Status updates persist to database
- [ ] Stats endpoint shows accurate counts
- [ ] Messages properly fetched and included in conversations
- [ ] Phone numbers extracted from tenant_profiles JSONB
- [ ] 70% test coverage
- [ ] README with setup instructions
- [ ] Docker setup (optional but valuable)

## Deliverables

1. **GitHub Repository** with:
   - Complete FastAPI application
   - Requirements.txt
   - .env.example
   - README with setup instructions
   - Test suite

2. **Documentation**:
   - How to run locally
   - Environment variable configuration
   - Example API calls with curl
   - Known limitations

## Common Pitfalls to Avoid

1. **Case Conversion**: Dashboard expects camelCase, database has snake_case
2. **Decimal Handling**: Return amounts as strings to avoid JSON issues
3. **Null Values**: Handle missing tenant_portion for non-Section 8
4. **Timezone**: Ensure timestamps include timezone info
5. **CORS**: Must be configured for dashboard to connect
6. **JSONB Phone Numbers**: Must parse the array structure correctly
7. **Missing Messages**: Don't forget to fetch from sms_messages table

## Questions to Consider

- Should we cache Collections Monitor calls?
- How often does priority score need recalculation?
- Should stats endpoint be cached?
- Do we need pagination for large result sets?
- Should we limit the number of messages returned per conversation?

## Starting Instructions

Reply with "Starting Backend API Integration - 48 hour timer begins" to start.

Once complete, the dashboard will show real delinquent tenants instead of mock data!