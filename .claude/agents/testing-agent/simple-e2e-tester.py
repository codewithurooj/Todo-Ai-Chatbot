"""
Simplified E2E Testing Script for Full-Stack Todo Application
Uses standard Python libraries (no Claude SDK required)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import subprocess

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not installed. Using environment variables directly.")


class E2ETestRunner:
    """Simplified E2E test runner using curl"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.results: List[Dict[str, Any]] = []
        self.jwt_token: str = ""
        self.user_id: str = ""
        self.task_ids: Dict[str, int] = {}

    def run_api_test(
        self,
        name: str,
        method: str,
        endpoint: str,
        expected_status: int,
        payload: Dict = None,
        use_auth: bool = False
    ) -> Dict[str, Any]:
        """Execute an API test using curl"""

        url = f"{self.api_url}{endpoint}"
        cmd = ["curl", "-X", method, "-s", "-w", "\n%{http_code}", url]

        # Add auth header if needed
        if use_auth and self.jwt_token:
            cmd.extend(["-H", f"Authorization: Bearer {self.jwt_token}"])

        # Add JSON payload for mutations
        if method in ["POST", "PUT", "PATCH"] and payload:
            cmd.extend([
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload)
            ])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            lines = result.stdout.strip().split('\n')
            status_code = int(lines[-1])
            body = '\n'.join(lines[:-1])

            # Try to parse JSON response
            try:
                body_json = json.loads(body) if body else None
            except json.JSONDecodeError:
                body_json = None

            passed = status_code == expected_status

            test_result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status": "passed" if passed else "failed",
                "expected_status": expected_status,
                "actual_status": status_code,
                "response": body_json or body[:200],
                "timestamp": datetime.now().isoformat()
            }

            self.results.append(test_result)

            # Print result
            icon = "[PASS]" if passed else "[FAIL]"
            print(f"{icon} {name}")
            print(f"  {method} {endpoint} -> {status_code} (expected {expected_status})")
            if not passed:
                print(f"  Response: {str(body_json or body)[:100]}")
            print()

            return {
                "passed": passed,
                "status_code": status_code,
                "body": body_json
            }

        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {name}")
            self.results.append({
                "name": name,
                "status": "error",
                "error": "Timeout after 30 seconds",
                "timestamp": datetime.now().isoformat()
            })
            return {"passed": False, "error": "timeout"}
        except Exception as e:
            print(f"[ERROR] {name} - {e}")
            self.results.append({
                "name": name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return {"passed": False, "error": str(e)}

    def generate_report(self):
        """Generate test report"""
        passed = sum(1 for r in self.results if r.get("status") == "passed")
        failed = sum(1 for r in self.results if r.get("status") == "failed")
        errors = sum(1 for r in self.results if r.get("status") == "error")
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        # Save JSON report
        report_dir = Path(__file__).parent / "reports"
        report_dir.mkdir(exist_ok=True)

        json_file = report_dir / "test-results.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # Generate markdown report
        md_report = f"""# E2E Test Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total Tests:** {total}
- **Passed:** {passed} [PASS]
- **Failed:** {failed} [FAIL]
- **Errors:** {errors} [ERROR]
- **Pass Rate:** {pass_rate:.1f}%

## Test Results

"""
        for result in self.results:
            status_icon = {"passed": "[PASS]", "failed": "[FAIL]", "error": "[ERROR]"}.get(result["status"], "[?]")
            md_report += f"### {status_icon} {result['name']}\n"
            md_report += f"**Status:** {result['status'].upper()}\n"
            md_report += f"**Time:** {result['timestamp']}\n"
            if "endpoint" in result:
                md_report += f"**Endpoint:** {result.get('method')} {result.get('endpoint')}\n"
                md_report += f"**Status Code:** {result.get('actual_status')} (expected {result.get('expected_status')})\n"
            if "error" in result:
                md_report += f"**Error:** {result['error']}\n"
            md_report += "\n"

        md_file = report_dir / "test-report.md"
        with open(md_file, 'w') as f:
            f.write(md_report)

        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} [PASS]")
        print(f"Failed: {failed} [FAIL]")
        print(f"Errors: {errors} [ERROR]")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print("=" * 80)
        print(f"\nReports saved:")
        print(f"  JSON: {json_file}")
        print(f"  Markdown: {md_file}")


def run_test_suite():
    """Run the complete E2E test suite"""

    # Load environment variables
    if DOTENV_AVAILABLE:
        load_dotenv(Path(__file__).parent / ".env")

    api_url = os.getenv("API_URL", "http://localhost:8000")
    test_email = os.getenv("TEST_USER_EMAIL", "test@example.com")
    test_password = os.getenv("TEST_USER_PASSWORD", "TestPassword123!")

    print("=" * 80)
    print("FULL-STACK TODO APP - E2E TEST SUITE")
    print("=" * 80)
    print(f"API URL: {api_url}")
    print(f"Test User: {test_email}")
    print("=" * 80)
    print()

    tester = E2ETestRunner(api_url)

    # Phase 1: Health Checks
    print("PHASE 1: Health & Connectivity")
    print("-" * 80)
    tester.run_api_test(
        "API Documentation Accessible",
        "GET",
        "/docs",
        200
    )

    # Phase 2: Authentication
    print("\nPHASE 2: User Authentication")
    print("-" * 80)

    # Signup
    signup_result = tester.run_api_test(
        "User Signup - Valid Credentials",
        "POST",
        "/api/auth/signup",
        201,
        payload={"email": test_email, "password": test_password}
    )

    # Try signup again (should fail - duplicate)
    tester.run_api_test(
        "User Signup - Duplicate Email (Should Fail)",
        "POST",
        "/api/auth/signup",
        400,
        payload={"email": test_email, "password": test_password}
    )

    # Login
    login_result = tester.run_api_test(
        "User Login - Correct Credentials",
        "POST",
        "/api/auth/signin",
        200,
        payload={"email": test_email, "password": test_password}
    )

    # Save JWT token and user_id if available
    if login_result.get("body") and isinstance(login_result["body"], dict):
        tester.jwt_token = login_result["body"].get("token", "")
        user_data = login_result["body"].get("user", {})
        tester.user_id = user_data.get("id", "")
        if tester.jwt_token:
            print(f"  [INFO] JWT token obtained (length: {len(tester.jwt_token)})")
        if tester.user_id:
            print(f"  [INFO] User ID: {tester.user_id}")

    # Login with wrong password
    tester.run_api_test(
        "User Login - Incorrect Password (Should Fail)",
        "POST",
        "/api/auth/signin",
        401,
        payload={"email": test_email, "password": "WrongPassword123!"}
    )

    # Phase 3: Task CRUD - Create
    print("\nPHASE 3: Task CRUD - Create")
    print("-" * 80)

    create_result = tester.run_api_test(
        "Create Task - Valid Data",
        "POST",
        f"/api/{tester.user_id}/tasks",
        201,
        payload={"title": "Test Task 1", "description": "This is a test task"},
        use_auth=True
    )

    # Save task ID if available
    if create_result.get("body") and isinstance(create_result["body"], dict):
        tester.task_ids["task1"] = create_result["body"].get("id")

    tester.run_api_test(
        "Create Task - Title Only",
        "POST",
        f"/api/{tester.user_id}/tasks",
        201,
        payload={"title": "Minimal Task"},
        use_auth=True
    )

    tester.run_api_test(
        "Create Task - Empty Title (Should Fail)",
        "POST",
        f"/api/{tester.user_id}/tasks",
        422,
        payload={"title": "", "description": "No title"},
        use_auth=True
    )

    # Phase 4: Task CRUD - Read
    print("\nPHASE 4: Task CRUD - Read")
    print("-" * 80)

    tester.run_api_test(
        "List All Tasks",
        "GET",
        f"/api/{tester.user_id}/tasks",
        200,
        use_auth=True
    )

    if tester.task_ids.get("task1"):
        tester.run_api_test(
            "Get Single Task - Valid ID",
            "GET",
            f"/api/{tester.user_id}/tasks/{tester.task_ids['task1']}",
            200,
            use_auth=True
        )

    tester.run_api_test(
        "Get Single Task - Non-existent ID",
        "GET",
        f"/api/{tester.user_id}/tasks/99999",
        404,
        use_auth=True
    )

    # Phase 5: Task CRUD - Update
    print("\nPHASE 5: Task CRUD - Update")
    print("-" * 80)

    if tester.task_ids.get("task1"):
        tester.run_api_test(
            "Update Task Title",
            "PUT",
            f"/api/{tester.user_id}/tasks/{tester.task_ids['task1']}",
            200,
            payload={"title": "Updated Task Title"},
            use_auth=True
        )

        tester.run_api_test(
            "Mark Task as Complete",
            "PATCH",
            f"/api/{tester.user_id}/tasks/{tester.task_ids['task1']}/complete",
            200,
            use_auth=True
        )

    # Phase 6: Task CRUD - Delete
    print("\nPHASE 6: Task CRUD - Delete")
    print("-" * 80)

    if tester.task_ids.get("task1"):
        tester.run_api_test(
            "Delete Task - Valid ID",
            "DELETE",
            f"/api/{tester.user_id}/tasks/{tester.task_ids['task1']}",
            204,
            use_auth=True
        )

    tester.run_api_test(
        "Delete Non-existent Task",
        "DELETE",
        f"/api/{tester.user_id}/tasks/99999",
        404,
        use_auth=True
    )

    # Phase 7: Security
    print("\nPHASE 7: Security & Validation")
    print("-" * 80)

    # Test without authentication
    original_token = tester.jwt_token
    tester.jwt_token = ""
    tester.run_api_test(
        "Access Protected Endpoint Without Token (Should Fail)",
        "GET",
        f"/api/{tester.user_id}/tasks",
        401
    )
    tester.jwt_token = original_token

    # Generate final report
    print()
    tester.generate_report()


if __name__ == "__main__":
    try:
        run_test_suite()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
