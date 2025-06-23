# API Reference - Housing Authority Assistant

Complete API documentation for the Housing Authority Assistant backend.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API uses OpenAI API key authentication configured via environment variables. No additional authentication is required for client requests.

## Endpoints

### Health Check

**GET** `/health`

Check if the API server is running.

**Response:**
```json
{
  "status": "ok"
}
```

### Chat Endpoint

**POST** `/chat`

Main endpoint for agent interactions.

**Request Body:**
```json
{
  "conversation_id": "string (optional)",
  "message": "string (required)"
}
```

**Response:**
```json
{
  "conversation_id": "string",
  "current_agent": "string",
  "messages": [
    {
      "content": "string",
      "agent": "string"
    }
  ],
  "events": [
    {
      "id": "string",
      "type": "string",
      "agent": "string",
      "content": "string",
      "metadata": "object",
      "timestamp": "number"
    }
  ],
  "context": {
    "t_code": "string",
    "participant_name": "string",
    "phone_number": "string",
    "email": "string",
    "participant_type": "string",
    "language": "string",
    "unit_address": "string",
    "inspection_id": "string",
    "inspection_date": "string",
    "inspector_name": "string",
    "door_codes": "string",
    "payment_method": "string",
    "documentation_pending": "boolean",
    "hps_worker_name": "string",
    "appointment_date": "string",
    "case_type": "string",
    "account_number": "string"
  },
  "agents": [
    {
      "name": "string",
      "description": "string",
      "handoffs": ["string"],
      "tools": ["string"],
      "input_guardrails": ["string"]
    }
  ],
  "guardrails": [
    {
      "id": "string",
      "name": "string",
      "input": "string",
      "reasoning": "string",
      "passed": "boolean",
      "timestamp": "number"
    }
  ]
}
```

## Agent Types

### Triage Agent
- **Name**: "Triage Agent"
- **Purpose**: Routes requests to appropriate specialists
- **Tools**: None (routing only)
- **Handoffs**: All other agents

### Inspection Agent
- **Name**: "Inspection Agent"
- **Purpose**: HQS inspection management
- **Tools**: 
  - `schedule_inspection`
  - `reschedule_inspection`
  - `cancel_inspection`
  - `check_inspection_status`
  - `get_inspection_requirements`
  - `update_door_codes`

### Landlord Services Agent
- **Name**: "Landlord Services Agent"
- **Purpose**: Section 8 documentation and payment assistance
- **Tools**:
  - `update_payment_method`
  - `request_landlord_forms`
  - `housing_faq_lookup_tool`

### HPS Agent
- **Name**: "HPS Agent"
- **Purpose**: Housing Program Specialist appointments
- **Tools**:
  - `schedule_hps_appointment`
  - `request_income_reporting_form`

### General Information Agent
- **Name**: "General Information Agent"
- **Purpose**: Hours, contacts, and general questions
- **Tools**:
  - `housing_faq_lookup_tool`
  - `get_language_instructions`

## Context Fields

### Core Identity
- `t_code`: Primary case identifier
- `participant_name`: Full name
- `phone_number`: Contact phone
- `email`: Contact email
- `participant_type`: "tenant", "landlord", "unknown"

### Language & Preferences
- `language`: "english", "spanish", "mandarin"

### Housing Information
- `unit_address`: Property address
- `inspection_id`: HQS inspection identifier
- `inspection_date`: Scheduled inspection date
- `inspector_name`: Assigned inspector
- `door_codes`: Access codes for property

### Services
- `payment_method`: Landlord payment preference
- `documentation_pending`: Outstanding paperwork status
- `hps_worker_name`: Assigned HPS specialist
- `appointment_date`: Scheduled HPS appointment
- `case_type`: Type of housing assistance

### System
- `account_number`: Generated system identifier

## Event Types

### Message Events
```json
{
  "type": "message",
  "agent": "Agent Name",
  "content": "Response content"
}
```

### Handoff Events
```json
{
  "type": "handoff",
  "agent": "Source Agent",
  "content": "Source Agent -> Target Agent",
  "metadata": {
    "source_agent": "Source Agent",
    "target_agent": "Target Agent"
  }
}
```

### Tool Call Events
```json
{
  "type": "tool_call",
  "agent": "Agent Name",
  "content": "tool_name",
  "metadata": {
    "tool_args": "object"
  }
}
```

### Tool Output Events
```json
{
  "type": "tool_output",
  "agent": "Agent Name",
  "content": "Tool result",
  "metadata": {
    "tool_result": "any"
  }
}
```

### Context Update Events
```json
{
  "type": "context_update",
  "agent": "Agent Name",
  "content": "",
  "metadata": {
    "changes": "object"
  }
}
```

## Guardrails

### Relevance Guardrail
- **Purpose**: Ensures messages are housing authority related
- **Triggers**: Off-topic requests
- **Response**: Custom refusal with contact information

### Jailbreak Guardrail
- **Purpose**: Prevents system instruction bypass attempts
- **Triggers**: Prompt injection attempts
- **Response**: Standard security refusal

### Data Privacy Guardrail
- **Purpose**: Protects sensitive tenant information
- **Triggers**: Requests for private data
- **Response**: Privacy protection message

### Authority Limitation Guardrail
- **Purpose**: Prevents overstepping authority boundaries
- **Triggers**: Requests outside housing authority scope
- **Response**: Limitation explanation

### Language Support Guardrail
- **Purpose**: Ensures appropriate language responses
- **Triggers**: Language-specific requirements
- **Response**: Language-appropriate handling

## Error Handling

### Client Errors (4xx)

**400 Bad Request**
```json
{
  "detail": "Invalid request format"
}
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Server Errors (5xx)

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

No rate limiting is currently implemented, but it's recommended for production deployments.

## Example Usage

### JavaScript/TypeScript
```typescript
const chatResponse = await fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    conversation_id: existingId || undefined,
    message: userInput
  })
});

const data = await chatResponse.json();
console.log('Current agent:', data.current_agent);
console.log('Response:', data.messages[0]?.content);
```

### Python
```python
import requests

response = requests.post(
    'http://localhost:8000/chat',
    json={
        'conversation_id': existing_id,
        'message': 'I need to schedule an inspection'
    }
)

data = response.json()
print(f"Agent: {data['current_agent']}")
print(f"Response: {data['messages'][0]['content']}")
```

### cURL
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "optional-existing-id",
    "message": "I need help with Section 8 documentation"
  }'
```

## Development Tools

### Testing Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Chat test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test message"}'

# Inspection scheduling test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to schedule an HQS inspection"}'

# Multilingual test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Necesito programar una inspección"}'

# Guardrail test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather today?"}'
```

### Response Validation
```python
# Validate response structure
def validate_chat_response(response):
    required_fields = [
        'conversation_id', 'current_agent', 'messages', 
        'events', 'context', 'agents', 'guardrails'
    ]
    
    for field in required_fields:
        assert field in response, f"Missing field: {field}"
    
    assert isinstance(response['messages'], list)
    assert isinstance(response['events'], list)
    assert isinstance(response['context'], dict)
    assert isinstance(response['agents'], list)
    assert isinstance(response['guardrails'], list)
    
    print("✅ Response structure valid")
```

## OpenAPI Schema

The API automatically generates OpenAPI documentation available at:
- **Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Schema**: `http://localhost:8000/openapi.json`

## Support

For API issues or questions:
- Check server logs for detailed error information
- Verify OpenAI API key is correctly configured
- Ensure all required dependencies are installed
- Contact technical support for assistance