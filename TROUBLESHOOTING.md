# Collections Backend API - Troubleshooting & Known Limitations

This document covers current limitations, common issues, troubleshooting steps, and development notes for the Collections Backend API service.

## Known Limitations

### 1. Database & Performance Limitations

#### **Connection Pooling**
- **Issue**: No connection pooling implemented for Supabase
- **Impact**: May experience connection limits under high traffic
- **Workaround**: Service uses mock data fallback when Supabase unavailable
- **Future**: Implement connection pooling with `asyncpg` or similar

#### **Query Optimization**
- **Issue**: Queries not optimized for large datasets (>1000 records)
- **Impact**: Slower response times with large collections queues
- **Workaround**: Currently acceptable for expected dataset sizes
- **Future**: Add pagination, indexing strategies, and query optimization

#### **Real-time Updates**
- **Issue**: No real-time updates to frontend when data changes
- **Impact**: Dashboard may show stale data until manual refresh
- **Workaround**: Frontend can poll endpoints for updates
- **Future**: Implement WebSocket or Server-Sent Events

### 2. Data Processing Limitations

#### **Phone Number Priority**
- **Issue**: Always takes first active phone from JSONB array
- **Impact**: May not select optimal contact number
- **Current Logic**: 
  ```python
  # Takes first active number found
  for phone in phone_numbers:
      if phone.get('status') == 'active':
          return phone.get('number')
  ```
- **Future**: Implement priority-based selection (primary, mobile, home)

#### **Message History Pagination**
- **Issue**: No pagination for conversation messages
- **Impact**: Large conversations may cause slow responses/memory issues
- **Current**: Returns all messages for a conversation
- **Future**: Implement message pagination with limit/offset

#### **Collections Monitor Dependency**
- **Issue**: Optional integration - uses mock data when unavailable
- **Impact**: May show incomplete tenant reliability scores
- **Current**: Graceful degradation to mock data
- **Future**: Implement caching layer for Collections Monitor responses

### 3. API Design Limitations

#### **Rate Limiting**
- **Issue**: No rate limiting implemented
- **Impact**: Vulnerable to request flooding
- **Workaround**: Deploy behind API gateway with rate limiting
- **Future**: Implement per-client rate limiting middleware

#### **Authentication & Authorization**
- **Issue**: No authentication required for any endpoints
- **Impact**: All data accessible without credentials
- **Current**: Suitable for internal network deployment
- **Future**: Implement JWT/API key authentication

#### **Input Validation**
- **Issue**: Limited validation beyond Pydantic schemas
- **Impact**: May accept semantically invalid but structurally correct data
- **Example**: Priority scores > 100, negative amounts
- **Future**: Add business logic validation layer

### 4. Caching & Performance

#### **Statistics Calculation**
- **Issue**: Dashboard stats recalculated on every request
- **Impact**: Unnecessary database load for frequently accessed endpoint
- **Workaround**: Acceptable for current usage patterns
- **Future**: Implement Redis caching with TTL

#### **Collections Monitor Calls**
- **Issue**: No caching for external API calls
- **Impact**: Repeated calls to Collections Monitor for same tenant
- **Future**: Implement HTTP caching or Redis-based response caching

### 5. Development & Deployment Limitations

#### **Configuration Management**
- **Issue**: Environment variables not validated at startup
- **Impact**: Service may start with invalid configuration
- **Workaround**: Check logs for Supabase availability warnings
- **Future**: Add configuration validation middleware

#### **Error Monitoring**
- **Issue**: No structured error monitoring/alerting
- **Impact**: Production issues may go unnoticed
- **Workaround**: Monitor application logs manually
- **Future**: Integrate with Sentry, New Relic, or similar

---

## Common Issues & Troubleshooting

### 1. Supabase Connection Issues

#### **Symptoms**
- API returns mock data instead of real data
- Log message: "⚠️ Supabase credentials not configured - using mock data"
- 500 errors on data modification endpoints

#### **Diagnosis Steps**
```bash
# 1. Check environment variables
python -c "
import os
print('SUPABASE_URL:', os.getenv('SUPABASE_URL', 'NOT SET'))
print('SUPABASE_ANON_KEY:', os.getenv('SUPABASE_ANON_KEY', 'NOT SET')[:20] + '...' if os.getenv('SUPABASE_ANON_KEY') else 'NOT SET')
"

# 2. Test Supabase connection
python -c "
try:
    from supabase import create_client
    import os
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    result = client.table('collections_queue').select('count').execute()
    print('✅ Supabase connection successful')
except Exception as e:
    print('❌ Supabase connection failed:', str(e))
"
```

#### **Common Solutions**
1. **Missing Environment Variables**
   ```bash
   # Create .env file from template
   cp .env.example .env
   # Edit .env with actual Supabase credentials
   ```

2. **Invalid Supabase Credentials**
   - Check Supabase dashboard for correct URL/key
   - Verify anon key has necessary permissions
   - Ensure URL format: `https://[project-id].supabase.co`

3. **Network/Firewall Issues**
   ```bash
   # Test network connectivity
   curl -I https://[your-project].supabase.co
   ```

### 2. CORS Issues from Frontend

#### **Symptoms**
- Browser console errors: "Access to fetch blocked by CORS policy"
- OPTIONS preflight requests failing
- Frontend cannot access API endpoints

#### **Diagnosis Steps**
```bash
# Test CORS from browser console
fetch('http://localhost:8000/api/tenants')
  .then(r => r.json())
  .then(data => console.log('✅ API accessible:', data))
  .catch(e => console.error('❌ CORS issue:', e));
```

#### **Solutions**
1. **Configure Frontend URL**
   ```bash
   # In .env file
   FRONTEND_URL=http://localhost:3000
   
   # For multiple origins
   FRONTEND_URL=http://localhost:3000,https://dashboard.example.com
   ```

2. **Development CORS Issues**
   ```python
   # Temporary fix for development - add to main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Only for development!
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### 3. Mock Data vs Real Data Issues

#### **Symptoms**
- Dashboard shows same data repeatedly
- Data changes don't persist
- Unrealistic test data in production

#### **Identification**
```bash
# Check if service is using mock data
curl http://localhost:8000/api/tenants | jq '.[0].tenantName'
# Mock data will show consistent test names like "John Smith"

# Check service logs for mock data indicators
tail -f service.log | grep -i "mock\|supabase"
```

#### **Solutions**
1. **Verify Data Source**
   ```bash
   # Check main.py imports and SUPABASE_AVAILABLE flag
   python -c "
   import main
   print('Supabase available:', hasattr(main, 'supabase') and main.supabase is not None)
   "
   ```

2. **Force Supabase Connection**
   - Ensure `.env` file exists with correct credentials
   - Restart the service after environment changes
   - Check Supabase dashboard for table access permissions

### 4. Performance Issues

#### **Symptoms**
- Slow API responses (>2 seconds)
- Timeouts on large requests
- High memory usage

#### **Diagnosis**
```bash
# Test endpoint performance
time curl -s http://localhost:8000/api/conversations >/dev/null

# Monitor memory usage
python -c "
import psutil
import os
pid = os.getpid()
process = psutil.Process(pid)
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

#### **Solutions**
1. **Large Conversation History**
   - Limit message history in queries
   - Implement pagination for conversations
   - Add database indexes on frequently queried fields

2. **Database Query Optimization**
   ```sql
   -- Add indexes to Supabase tables
   CREATE INDEX IF NOT EXISTS idx_collections_queue_tenant_id ON collections_queue(tenant_id);
   CREATE INDEX IF NOT EXISTS idx_sms_conversations_tenant_profile_id ON sms_conversations(tenant_profile_id);
   CREATE INDEX IF NOT EXISTS idx_sms_messages_conversation_id ON sms_messages(conversation_id);
   ```

### 5. Test Failures

#### **Symptoms**
- Tests failing after code changes
- Coverage dropping unexpectedly
- Import errors in tests

#### **Diagnosis**
```bash
# Run tests with verbose output
python -m pytest tests/ -v --tb=short

# Check specific test failure
python -m pytest tests/test_api.py::TestTenantEndpoints::test_get_tenants_mock_data -v -s

# Verify test environment
python -c "
import sys
print('Python path:', sys.path)
try:
    import main, schemas
    print('✅ Imports successful')
except ImportError as e:
    print('❌ Import error:', e)
"
```

#### **Common Solutions**
1. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Issues**
   ```bash
   # Ensure pytest can find modules
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   
   # Or add to pytest.ini
   [tool:pytest]
   python_paths = .
   ```

3. **Mock Data Issues in Tests**
   - Verify mock functions return expected format
   - Check test assertions match actual response structure
   - Update tests when API response format changes

---

## Development Notes

### 1. Code Architecture Decisions

#### **Consolidated vs. Modular Structure**
- **Current**: Single `main.py` file with all endpoints
- **Rationale**: Simplified development and deployment for current scope
- **Trade-offs**: Less modular, but easier to maintain for small team
- **Future**: Refactor to modular structure when team/complexity grows

#### **Synchronous vs. Asynchronous Patterns**
- **Current**: Mixed sync/async patterns
- **Issue**: Some database calls are synchronous
- **Impact**: May limit concurrency under load
- **Future**: Convert all database operations to async

### 2. Database Schema Assumptions

#### **JSONB Phone Numbers**
```python
# Expected format in tenant_profiles.phone_numbers
[
    {
        "number": "+1234567890",
        "status": "active",
        "type": "mobile",
        "added_date": "2025-01-01"
    }
]
```

#### **Status Field Values**
```python
# Tenant statuses
TENANT_STATUSES = ["pending", "active", "resolved", "escalated"]

# Conversation statuses  
CONVERSATION_STATUSES = ["active", "paused", "resolved", "escalated"]

# Payment plan statuses
PAYMENT_PLAN_STATUSES = ["pending", "approved", "active", "completed", "cancelled"]
```

### 3. Integration Patterns

#### **Collections Monitor Integration**
```python
# Current pattern - synchronous HTTP calls
async def get_tenant_details(tenant_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MONITOR_API_URL}/tenant/{tenant_id}")
            return response.json() if response.status_code == 200 else None
        except httpx.RequestError:
            return None  # Graceful degradation
```

#### **Error Handling Philosophy**
- **Principle**: Fail gracefully with meaningful fallbacks
- **Implementation**: Mock data when external services unavailable
- **Logging**: Warn about degraded functionality, don't error
- **User Experience**: Always return valid response, even if partial data

### 4. Testing Strategy

#### **Test Coverage Goals**
- **Current**: 66.75% coverage
- **Target**: 70% (per specification)
- **Focus Areas**: Error paths, edge cases, data transformation
- **Exclusions**: External service integration (mocked)

#### **Mock Data Consistency**
- Mock data matches expected production schema
- Realistic test scenarios (various tenant states)
- Consistent UUIDs for predictable testing
- Representative edge cases (missing phone, null values)

---

## Production Readiness Checklist

### Before Deployment
- [ ] Environment variables configured and validated
- [ ] Supabase connection tested with production credentials
- [ ] Collections Monitor integration tested (or mock fallback confirmed)
- [ ] CORS configured for production frontend domain
- [ ] All tests passing with >70% coverage
- [ ] Health endpoint accessible for monitoring
- [ ] Logging configured appropriately for production
- [ ] Error handling tested under various failure scenarios

### Monitoring & Maintenance
- [ ] Set up log aggregation and monitoring
- [ ] Configure alerts for service health
- [ ] Monitor API response times and error rates
- [ ] Regular database performance review
- [ ] Periodic dependency updates
- [ ] Backup and recovery procedures documented

### Scaling Considerations
- [ ] Database connection pooling implementation
- [ ] Response caching strategy
- [ ] Load balancer configuration
- [ ] Rate limiting implementation
- [ ] Horizontal scaling architecture planning

---

This document should be updated as new limitations are discovered or existing ones are resolved.