# Spec Writer Skill

## Purpose
Rapidly generate comprehensive technical specifications following spec-driven development principles.

## Capabilities
- Create detailed feature specifications
- Define API contracts
- Write user stories with acceptance criteria
- Document system architecture
- Generate test scenarios
- Produce clear, structured documentation

## Input Parameters
```typescript
{
  type: 'feature' | 'api' | 'component' | 'system';
  name: string;
  description: string;
  requirements: string[];
}
```

## Output Format

### Feature Specification
```markdown
# Feature: [Name]

## Overview
Brief description of what this feature does and why it's needed.

## User Stories
- As a [user type], I want [goal] so that [benefit]
- As a [user type], I want [goal] so that [benefit]

## Requirements

### Functional Requirements
1. The system SHALL...
2. The system SHALL...

### Non-Functional Requirements
1. Performance: Response time < 3s
2. Security: Data encrypted at rest
3. Usability: Accessible (WCAG AA)

## Technical Specification

### Data Models
\`\`\`typescript
interface Model {
  id: string;
  field: type;
}
\`\`\`

### API Endpoints
- `GET /resource` - Description
- `POST /resource` - Description

### UI Components
- Component 1: Purpose
- Component 2: Purpose

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All tests pass
- [ ] Code review approved
- [ ] Documentation updated

## Test Scenarios

### Happy Path
1. User does X
2. System responds with Y
3. Result: Success

### Edge Cases
1. Scenario: Empty input
   - Expected: Error message
2. Scenario: Invalid data
   - Expected: Validation error

## Dependencies
- Service A
- Library B

## Risks & Mitigation
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Risk 1 | High | Medium | Strategy |

## Timeline
- Design: 1 day
- Implementation: 3 days
- Testing: 1 day
- Deployment: 0.5 days

## Success Metrics
- Metric 1: Target value
- Metric 2: Target value
```

## API Specification Template

```markdown
# API Specification: [Endpoint Name]

## Endpoint
`METHOD /api/path/{param}`

## Description
What this endpoint does and when to use it.

## Authentication
- Required: Yes/No
- Type: Bearer token / API key / None

## Request

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param | string | Yes | Description |

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | number | No | 10 | Max results |

### Request Body
\`\`\`json
{
  "field": "value",
  "nested": {
    "field": "value"
  }
}
\`\`\`

### Validation Rules
- `field`: Required, min length 3
- `nested.field`: Optional, enum [a, b, c]

## Response

### Success Response (200 OK)
\`\`\`json
{
  "data": {
    "id": "123",
    "field": "value"
  },
  "meta": {
    "timestamp": "2025-01-15T10:00:00Z"
  }
}
\`\`\`

### Error Responses

#### 400 Bad Request
\`\`\`json
{
  "error": "Validation failed",
  "details": {
    "field": ["Error message"]
  }
}
\`\`\`

#### 401 Unauthorized
\`\`\`json
{
  "error": "Authentication required"
}
\`\`\`

#### 404 Not Found
\`\`\`json
{
  "error": "Resource not found"
}
\`\`\`

#### 500 Internal Server Error
\`\`\`json
{
  "error": "Internal server error"
}
\`\`\`

## Rate Limiting
- Limit: 100 requests per minute
- Header: `X-RateLimit-Remaining`

## Example Usage

### cURL
\`\`\`bash
curl -X POST https://api.example.com/api/path \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
\`\`\`

### JavaScript
\`\`\`javascript
const response = await fetch('https://api.example.com/api/path', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ field: 'value' })
});
const data = await response.json();
\`\`\`

### Python
\`\`\`python
import requests

response = requests.post(
    'https://api.example.com/api/path',
    headers={'Authorization': 'Bearer token'},
    json={'field': 'value'}
)
data = response.json()
\`\`\`

## Testing

### Unit Tests
\`\`\`python
def test_endpoint_success():
    response = client.post('/api/path', json={'field': 'value'})
    assert response.status_code == 200
    assert response.json()['data']['id'] is not None
\`\`\`

### Integration Tests
\`\`\`python
def test_endpoint_with_auth():
    response = client.post(
        '/api/path',
        headers={'Authorization': 'Bearer valid_token'},
        json={'field': 'value'}
    )
    assert response.status_code == 200
\`\`\`

## Notes
- Additional considerations
- Known limitations
- Future enhancements
```

## Component Specification Template

```markdown
# Component: [Name]

## Purpose
What this component does and why it exists.

## Props/Parameters
\`\`\`typescript
interface Props {
  required: string;
  optional?: number;
  callback: (data: Type) => void;
}
\`\`\`

## States
- State 1: Description
- State 2: Description

## Behavior
1. When X happens, do Y
2. When Z happens, do A

## Styling
- Theme variables used
- CSS classes applied
- Responsive breakpoints

## Accessibility
- ARIA labels
- Keyboard navigation
- Screen reader support

## Usage Example
\`\`\`tsx
<Component
  required="value"
  optional={42}
  callback={(data) => console.log(data)}
/>
\`\`\`

## Testing
- Test 1: Render with props
- Test 2: User interaction
- Test 3: Edge cases
```

## Usage Example

```markdown
**User**: Use the Spec Writer skill to create a specification for a user authentication API endpoint.

**Claude**: I'll create a comprehensive API specification.

[Generates detailed spec with all sections]

Created specification includes:
- Endpoint details (POST /api/auth/login)
- Request/response formats
- Error handling
- Rate limiting
- Code examples in 3 languages
- Test scenarios
- Security considerations
```

## Best Practices

### 1. Be Specific
❌ "The system should be fast"
✅ "The system SHALL respond within 3 seconds for 95% of requests"

### 2. Use Standard Keywords
- **SHALL** - Mandatory requirement
- **SHOULD** - Recommended but not mandatory
- **MAY** - Optional

### 3. Include Examples
Always provide:
- Code examples
- Request/response samples
- Usage scenarios

### 4. Define Success Criteria
Clear, measurable acceptance criteria:
- [ ] Feature works as described
- [ ] Tests pass (unit + integration)
- [ ] Performance meets targets
- [ ] Security review completed

### 5. Consider Edge Cases
- Empty inputs
- Invalid data
- Timeout scenarios
- Network failures
- Concurrent access

## Quality Checklist

A good specification should have:
- [ ] Clear purpose and overview
- [ ] Detailed requirements
- [ ] Technical implementation details
- [ ] Acceptance criteria
- [ ] Test scenarios
- [ ] Error handling
- [ ] Code examples
- [ ] Dependencies listed
- [ ] Success metrics defined
- [ ] Timeline estimated

## Integration with Development

Specs enable:
1. **Clear Communication** - Everyone understands requirements
2. **Parallel Development** - Teams can work independently
3. **Better Testing** - Test scenarios are predefined
4. **Quality Assurance** - Acceptance criteria are explicit
5. **Documentation** - Specs become living documentation

## Reusability

Use this skill for:
- Feature specifications
- API documentation
- Component design docs
- System architecture docs
- Integration specifications
- Security requirements
- Performance requirements

## Time Efficiency

- Manual spec writing: 2-3 hours
- With this skill: 5-10 minutes
- **Time saved: 95%+**

## Success Metrics

- Spec is complete (all sections filled)
- Requirements are clear and testable
- Examples are provided
- Edge cases are considered
- Acceptance criteria are measurable
- Can be implemented directly from spec

---

**This skill makes spec-driven development effortless!** 📋
