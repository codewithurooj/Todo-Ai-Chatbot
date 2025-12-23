# E2E Testing Agent

An autonomous end-to-end testing agent for the Full-Stack Todo Application, built with the Claude Agent SDK.

## Overview

This testing agent uses Claude's AI capabilities to autonomously test your full-stack todo application, including:

- CRUD operations for tasks
- User authentication flows
- Data validation and error handling
- Security testing (SQL injection, XSS attempts)
- API response schema validation
- Comprehensive test reporting

## Architecture

```
testing-agent/
├── e2e-tester.py           # Main agent script with custom tools
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
├── tests/
│   ├── fixtures.json      # Test data (users, tasks, edge cases)
│   └── test-cases.json    # Test scenarios and configurations
└── reports/
    ├── test-results.json  # Detailed test results (generated)
    └── test-report.md     # Human-readable summary (generated)
```

## Custom Testing Tools

The agent includes 4 custom MCP tools:

### 1. `run_api_test`
Executes API requests and validates responses.

**Parameters:**
- `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
- `endpoint`: API endpoint path
- `payload`: Request body (for POST/PUT/PATCH)
- `expected_status`: Expected HTTP status code
- `auth_token`: JWT token for authentication

**Returns:** Test result with pass/fail status and response details

### 2. `validate_response_schema`
Validates API responses against expected schemas.

**Parameters:**
- `response_body`: JSON response from API
- `expected_fields`: List of required field names
- `field_types`: Dict mapping fields to expected types

**Returns:** Validation result with detailed error messages

### 3. `log_test_result`
Records test outcomes to a JSON file.

**Parameters:**
- `test_name`: Name/description of the test
- `status`: Test status (passed, failed, skipped, error)
- `details`: Detailed test information
- `metadata`: Additional test metadata

**Returns:** Confirmation of logged result

### 4. `generate_test_report`
Generates summary reports from test results.

**Parameters:**
- `report_format`: Output format (json, markdown)

**Returns:** Formatted test report with statistics

## Installation

### 1. Install Python Dependencies

```bash
cd testing-agent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required environment variables:**

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-your-api-key

# Application URLs
API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Test credentials
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=TestPassword123!
```

### 3. Ensure Backend is Running

```bash
# In backend directory
cd ../backend
uvicorn app.main:app --reload
```

## Usage

### Run Complete Test Suite

Execute all end-to-end tests:

```bash
python e2e-tester.py
```

### View Test Results

**JSON format (detailed):**
```bash
cat reports/test-results.json
```

**Markdown format (summary):**
```bash
cat reports/test-report.md
```

### Run Specific Test Phases

Modify `tests/test-cases.json` to customize which tests run:

```json
{
  "test_phases": [
    {
      "phase": 1,
      "name": "Health & Connectivity",
      "tests": [...]
    }
  ]
}
```

## Test Coverage

The agent tests the following areas:

### ✅ Health & Connectivity
- API documentation accessibility
- Health check endpoints
- CORS configuration

### ✅ Authentication
- User signup (valid/invalid)
- User login (correct/incorrect credentials)
- JWT token generation
- Protected endpoint access control

### ✅ Task CRUD Operations
- **Create:** Valid/invalid tasks, validation errors
- **Read:** List all, get single, non-existent resources
- **Update:** Modify title, description, completion status
- **Delete:** Remove tasks, handle non-existent IDs

### ✅ Data Validation
- Empty/null fields
- Invalid data types
- Boundary conditions (very long strings)
- Special characters and unicode

### ✅ Security Testing
- Unauthenticated access attempts
- SQL injection attempts
- XSS attack vectors
- Malformed requests

## Test Report Example

```markdown
# E2E Test Report

**Generated:** 2025-12-14 15:30:00

## Summary

- **Total Tests:** 25
- **Passed:** 23 ✓
- **Failed:** 1 ✗
- **Errors:** 0 ⚠
- **Skipped:** 1 ○
- **Pass Rate:** 92.0%

## Test Results

### ✓ API Documentation Accessible
**Status:** PASSED
**Time:** 2025-12-14T15:30:01
**Details:** GET /docs returned 200 OK

### ✗ Delete Already Deleted Task
**Status:** FAILED
**Time:** 2025-12-14T15:30:15
**Details:** Expected 404, got 500
```

## Customization

### Add New Test Cases

Edit `tests/test-cases.json`:

```json
{
  "phase": 8,
  "name": "Custom Tests",
  "tests": [
    {
      "name": "My Custom Test",
      "method": "POST",
      "endpoint": "/api/custom",
      "payload": {...},
      "expected_status": 201
    }
  ]
}
```

### Modify Test Data

Edit `tests/fixtures.json`:

```json
{
  "tasks": [
    {
      "title": "New test task",
      "description": "Custom test data",
      "is_completed": false
    }
  ]
}
```

### Extend Agent System Prompt

In `e2e-tester.py`, modify the `system_prompt.append` section:

```python
system_prompt={
    "type": "preset",
    "preset": "claude_code",
    "append": """
Your custom testing instructions here...
"""
}
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          cd testing-agent
          pip install -r requirements.txt
      - name: Run E2E tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          API_URL: ${{ secrets.API_URL }}
        run: |
          cd testing-agent
          python e2e-tester.py
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: testing-agent/reports/
```

## Troubleshooting

### Agent Not Running

**Issue:** `ImportError: No module named 'claude_agent_sdk'`

**Solution:**
```bash
pip install --upgrade claude-agent-sdk
```

### API Connection Errors

**Issue:** `Could not verify API`

**Solution:**
1. Check backend is running: `curl http://localhost:8000/docs`
2. Verify `API_URL` in `.env` matches your backend
3. Check firewall/network settings

### Authentication Failures

**Issue:** All protected endpoints return 401

**Solution:**
1. Check test credentials in `.env`
2. Verify Better Auth is configured
3. Ensure signup endpoint creates valid JWT tokens

### Test Timeouts

**Issue:** Tests hanging or timing out

**Solution:**
1. Increase timeout in `.env`: `TEST_TIMEOUT=60`
2. Check database connectivity
3. Ensure backend has sufficient resources

## Advanced Features

### Custom Tool Development

Add new tools to `e2e-tester.py`:

```python
@tool("my_custom_tool", "Tool description", {
    "param1": str,
    "param2": int
})
async def my_custom_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    # Your tool implementation
    return {
        "content": [{
            "type": "text",
            "text": "Tool result"
        }]
    }
```

### Session-Based Testing

The agent maintains context across test phases, enabling:
- Token persistence (login once, use everywhere)
- Resource ID tracking (create task, reference later)
- State validation (verify changes persist)

### Parallel Test Execution

For faster testing, run multiple agents in parallel:

```python
async def run_parallel_tests():
    tasks = [
        run_auth_tests(),
        run_crud_tests(),
        run_validation_tests()
    ]
    await asyncio.gather(*tasks)
```

## Best Practices

1. **Clean Test Data:** Always delete test resources after each run
2. **Isolated Tests:** Each test should be independent
3. **Clear Naming:** Use descriptive test names
4. **Log Everything:** Record all test outcomes for debugging
5. **Version Control:** Track test case changes in git

## Contributing

To add new features to the testing agent:

1. Create new custom tools in `e2e-tester.py`
2. Add test cases to `tests/test-cases.json`
3. Update fixtures in `tests/fixtures.json`
4. Document changes in this README
5. Test your changes thoroughly

## Support

For issues or questions:

1. Check existing test results in `reports/`
2. Review agent logs for error details
3. Consult Claude Agent SDK documentation
4. Open an issue in the project repository

## License

Part of the Full-Stack Todo Application project.
