"""
End-to-End Testing Agent for Full-Stack Todo Application
Uses Claude Agent SDK to autonomously test CRUD operations, authentication, and validation.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
import subprocess

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    tool,
    create_sdk_mcp_server
)


# ============================================================================
# CUSTOM TESTING TOOLS
# ============================================================================

@tool("run_api_test", "Test API endpoints with given parameters", {
    "method": str,
    "endpoint": str,
    "payload": dict,
    "expected_status": int,
    "auth_token": str
})
async def run_api_test(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test individual API endpoints with curl.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        endpoint: API endpoint path (e.g., /api/tasks)
        payload: Request body for POST/PUT/PATCH
        expected_status: Expected HTTP status code
        auth_token: Optional JWT token for authentication

    Returns:
        Test result with status, body, and pass/fail indication
    """
    method = args["method"]
    endpoint = args["endpoint"]
    payload = args.get("payload", {})
    expected_status = args["expected_status"]
    auth_token = args.get("auth_token", "")

    # Construct full URL
    base_url = os.getenv("API_URL", "http://localhost:8000")
    url = f"{base_url}{endpoint}"

    # Build curl command
    cmd = ["curl", "-X", method, "-s", "-w", "\n%{http_code}", url]

    # Add authentication header if provided
    if auth_token:
        cmd.extend(["-H", f"Authorization: Bearer {auth_token}"])

    # Add JSON content type and payload for mutations
    if method in ["POST", "PUT", "PATCH"] and payload:
        cmd.extend([
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload)
        ])

    try:
        # Execute curl command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Parse response (last line is status code)
        lines = result.stdout.strip().split('\n')
        status_code = int(lines[-1])
        body = '\n'.join(lines[:-1])

        # Determine if test passed
        passed = status_code == expected_status

        # Try to parse JSON response
        try:
            body_json = json.loads(body) if body else None
        except json.JSONDecodeError:
            body_json = None

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "expected_status": expected_status,
                    "passed": passed,
                    "body": body_json or body[:500],
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            }]
        }
    except subprocess.TimeoutExpired:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "error": "Request timeout after 30 seconds",
                    "endpoint": endpoint,
                    "method": method,
                    "passed": False
                }, indent=2)
            }],
            "is_error": True
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "error": f"Test execution failed: {str(e)}",
                    "endpoint": endpoint,
                    "method": method,
                    "passed": False
                }, indent=2)
            }],
            "is_error": True
        }


@tool("validate_response_schema", "Validate API response against expected schema", {
    "response_body": dict,
    "expected_fields": list,
    "field_types": dict
})
async def validate_response_schema(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that API response matches expected schema.

    Args:
        response_body: The JSON response from API
        expected_fields: List of required field names
        field_types: Dict mapping field names to expected types

    Returns:
        Validation result with detailed findings
    """
    response_body = args["response_body"]
    expected_fields = args["expected_fields"]
    field_types = args.get("field_types", {})

    validation_errors = []

    # Check for missing required fields
    for field in expected_fields:
        if field not in response_body:
            validation_errors.append(f"Missing required field: {field}")

    # Check field types
    for field, expected_type in field_types.items():
        if field in response_body:
            actual_type = type(response_body[field]).__name__
            if actual_type != expected_type:
                validation_errors.append(
                    f"Field '{field}': expected {expected_type}, got {actual_type}"
                )

    passed = len(validation_errors) == 0

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "passed": passed,
                "errors": validation_errors,
                "validated_fields": list(field_types.keys()),
                "response_summary": {
                    k: type(v).__name__ for k, v in response_body.items()
                }
            }, indent=2)
        }]
    }


@tool("log_test_result", "Log test results to file", {
    "test_name": str,
    "status": str,
    "details": str,
    "metadata": dict
})
async def log_test_result(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log test results to a JSON file for reporting.

    Args:
        test_name: Name/description of the test
        status: Test status (passed, failed, skipped, error)
        details: Detailed test information
        metadata: Additional test metadata

    Returns:
        Confirmation of logged result
    """
    test_name = args["test_name"]
    status = args["status"]
    details = args["details"]
    metadata = args.get("metadata", {})

    timestamp = datetime.now().isoformat()
    report_dir = Path(__file__).parent / "reports"
    report_file = report_dir / "test-results.json"

    result_entry = {
        "timestamp": timestamp,
        "test_name": test_name,
        "status": status,
        "details": details,
        "metadata": metadata
    }

    try:
        # Ensure reports directory exists
        report_dir.mkdir(parents=True, exist_ok=True)

        # Load existing results or create new list
        if report_file.exists():
            with open(report_file, 'r') as f:
                results = json.load(f)
        else:
            results = []

        # Append new result
        results.append(result_entry)

        # Write back to file
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Logged test result: {test_name} - {status.upper()}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Error logging result: {str(e)}"
            }],
            "is_error": True
        }


@tool("generate_test_report", "Generate summary test report", {
    "report_format": str
})
async def generate_test_report(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary report from all logged test results.

    Args:
        report_format: Output format (json, markdown, html)

    Returns:
        Formatted test report
    """
    report_format = args.get("report_format", "markdown")
    report_dir = Path(__file__).parent / "reports"
    results_file = report_dir / "test-results.json"

    try:
        if not results_file.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": "No test results found. Run tests first."
                }]
            }

        with open(results_file, 'r') as f:
            results = json.load(f)

        # Calculate statistics
        total_tests = len(results)
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = sum(1 for r in results if r["status"] == "failed")
        errors = sum(1 for r in results if r["status"] == "error")
        skipped = sum(1 for r in results if r["status"] == "skipped")

        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0

        if report_format == "markdown":
            report = f"""# E2E Test Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total Tests:** {total_tests}
- **Passed:** {passed} ✓
- **Failed:** {failed} ✗
- **Errors:** {errors} ⚠
- **Skipped:** {skipped} ○
- **Pass Rate:** {pass_rate:.1f}%

## Test Results

"""
            for result in results:
                status_icon = {
                    "passed": "✓",
                    "failed": "✗",
                    "error": "⚠",
                    "skipped": "○"
                }.get(result["status"], "?")

                report += f"### {status_icon} {result['test_name']}\n"
                report += f"**Status:** {result['status'].upper()}\n"
                report += f"**Time:** {result['timestamp']}\n"
                report += f"**Details:** {result['details']}\n\n"

            # Save markdown report
            report_file = report_dir / "test-report.md"
            with open(report_file, 'w') as f:
                f.write(report)

            return {
                "content": [{
                    "type": "text",
                    "text": f"Report generated: {report_file}\n\n{report}"
                }]
            }
        else:
            # JSON format
            summary = {
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total": total_tests,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "skipped": skipped,
                    "pass_rate": round(pass_rate, 2)
                },
                "results": results
            }
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(summary, indent=2)
                }]
            }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error generating report: {str(e)}"
            }],
            "is_error": True
        }


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

async def create_testing_agent() -> ClaudeAgentOptions:
    """
    Create and configure the E2E testing agent with custom tools.

    Returns:
        Configured ClaudeAgentOptions for the testing agent
    """

    # Create MCP server with custom testing tools
    testing_server = create_sdk_mcp_server(
        name="testing",
        version="1.0.0",
        tools=[
            run_api_test,
            validate_response_schema,
            log_test_result,
            generate_test_report
        ]
    )

    # Configure agent options
    options = ClaudeAgentOptions(
        mcp_servers={"test": testing_server},
        allowed_tools=[
            # File operations
            "Read",
            "Write",
            "Glob",
            "Grep",
            # System operations
            "Bash",
            # Custom testing tools
            "mcp__test__run_api_test",
            "mcp__test__validate_response_schema",
            "mcp__test__log_test_result",
            "mcp__test__generate_test_report"
        ],
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": """
You are an expert End-to-End Testing Agent for a full-stack todo application.

**Application Stack:**
- Frontend: Next.js 16+ with TypeScript and Tailwind CSS
- Backend: FastAPI with SQLModel and PostgreSQL
- Auth: Better Auth with JWT tokens

**Your Testing Responsibilities:**

1. **CRUD Operations Testing**
   - Create, Read, Update, Delete operations for tasks
   - Verify correct HTTP status codes
   - Validate response schemas match API contracts
   - Test with valid and invalid data

2. **Authentication Testing**
   - User signup and signin flows
   - JWT token generation and validation
   - Protected endpoint access control
   - Token expiration handling

3. **Data Validation Testing**
   - Empty/null field handling
   - Invalid data types
   - Boundary conditions
   - Special characters and edge cases

4. **Error Handling Testing**
   - 404 for non-existent resources
   - 400 for bad requests
   - 401/403 for authentication issues
   - 500 for server errors

5. **Test Reporting**
   - Log all test results with timestamps
   - Provide clear pass/fail indicators
   - Generate comprehensive summary reports
   - Include detailed error messages

**Testing Best Practices:**
- Always clean up test data after tests
- Use the custom MCP tools for API testing
- Validate response schemas for all endpoints
- Log results immediately after each test
- Generate a final summary report
- Report any unexpected behavior immediately

**Available Custom Tools:**
- `run_api_test`: Execute API requests and verify responses
- `validate_response_schema`: Validate JSON response structure
- `log_test_result`: Record test outcomes
- `generate_test_report`: Create summary reports
"""
        },
        permission_mode="acceptEdits",
        cwd=str(Path(__file__).parent),
        env={
            "API_URL": os.getenv("API_URL", "http://localhost:8000"),
            "FRONTEND_URL": os.getenv("FRONTEND_URL", "http://localhost:3000"),
            "TEST_USER_EMAIL": os.getenv("TEST_USER_EMAIL", "test@example.com"),
            "TEST_USER_PASSWORD": os.getenv("TEST_USER_PASSWORD", "TestPassword123!")
        }
    )

    return options


# ============================================================================
# TEST SUITE EXECUTION
# ============================================================================

async def run_test_suite():
    """
    Execute the comprehensive E2E test suite.
    """

    options = await create_testing_agent()

    # Load test cases from file if exists
    test_cases_file = Path(__file__).parent / "tests" / "test-cases.json"

    if test_cases_file.exists():
        with open(test_cases_file, 'r') as f:
            test_cases_config = json.load(f)
            test_prompt = test_cases_config.get("prompt", "")
    else:
        # Default comprehensive test prompt
        test_prompt = """
Execute a comprehensive end-to-end test suite for the full-stack todo application.

**Test Suite Structure:**

## Phase 1: Health & Connectivity
1. Check backend API is running (GET /docs or /health)
2. Verify API documentation is accessible
3. Test CORS configuration

## Phase 2: Authentication Flow
1. Create new user account (POST /api/auth/signup)
   - Test with valid credentials
   - Test with duplicate email (should fail)
   - Validate JWT token in response
2. User login (POST /api/auth/signin)
   - Test with correct credentials
   - Test with incorrect password (should fail)
   - Validate JWT token returned
3. Save JWT token for subsequent tests

## Phase 3: Task CRUD Operations
Use the JWT token from authentication for all requests.

1. **Create Tasks** (POST /api/tasks)
   - Create task with title only
   - Create task with title and description
   - Create task with all fields
   - Test validation: empty title (should fail)
   - Test validation: invalid data types (should fail)

2. **Read Tasks** (GET /api/tasks)
   - List all tasks
   - Verify created tasks are in the list
   - Validate response schema

3. **Read Single Task** (GET /api/tasks/{id})
   - Get each created task by ID
   - Test with non-existent ID (should return 404)
   - Validate response schema

4. **Update Tasks** (PUT/PATCH /api/tasks/{id})
   - Update task title
   - Update task description
   - Mark task as complete
   - Unmark task as complete
   - Test with invalid ID (should return 404)

5. **Delete Tasks** (DELETE /api/tasks/{id})
   - Delete a task
   - Verify it's removed from list
   - Test deleting non-existent task (should return 404)

## Phase 4: Data Validation
1. Test boundary conditions
   - Very long title (>1000 chars)
   - Empty strings vs null
   - Special characters in title/description
2. Test data persistence
   - Create task, logout, login, verify task exists

## Phase 5: Error Handling
1. Test unauthenticated access to protected endpoints
2. Test malformed JSON requests
3. Test missing required fields
4. Test invalid Content-Type headers

**For Each Test:**
1. Use `run_api_test` tool to execute the request
2. Use `validate_response_schema` to verify response structure
3. Use `log_test_result` to record the outcome
4. Report immediate failures

**After All Tests:**
1. Use `generate_test_report` to create summary
2. Report total pass/fail statistics
3. Highlight any critical failures
"""

    # Clear previous test results
    report_file = Path(__file__).parent / "reports" / "test-results.json"
    if report_file.exists():
        report_file.unlink()

    print("=" * 80)
    print("STARTING END-TO-END TEST SUITE")
    print("=" * 80)
    print(f"API URL: {os.getenv('API_URL', 'http://localhost:8000')}")
    print(f"Frontend URL: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}")
    print("=" * 80)
    print()

    # Run the agent with the test suite
    async with ClaudeSDKClient(options=options) as client:
        await client.query(test_prompt)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        print()

            # Check for completion or errors
            if hasattr(message, 'subtype'):
                if message.subtype == 'success':
                    print("\n" + "=" * 80)
                    print("TEST SUITE COMPLETED SUCCESSFULLY")
                    print("=" * 80)
                elif message.subtype in ['error', 'error_during_execution']:
                    print("\n" + "=" * 80)
                    print("TEST SUITE ENCOUNTERED ERRORS")
                    print("=" * 80)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """
    Main entry point for the E2E testing agent.
    """

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / ".env")
    except ImportError:
        print("Warning: python-dotenv not installed, using environment variables")

    # Ensure reports directory exists
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Check API availability
    api_url = os.getenv("API_URL", "http://localhost:8000")
    print(f"Checking API availability at {api_url}...")

    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"{api_url}/docs"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout == "200":
            print("✓ API is accessible")
        else:
            print(f"⚠ Warning: API returned status {result.stdout}")
    except Exception as e:
        print(f"⚠ Warning: Could not verify API: {e}")

    print()

    # Run the test suite
    await run_test_suite()


if __name__ == "__main__":
    asyncio.run(main())
