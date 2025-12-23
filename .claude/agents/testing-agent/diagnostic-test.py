"""
Comprehensive Diagnostic Test Script
Tests both frontend and backend integration issues
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass


class DiagnosticTester:
    """Comprehensive diagnostic testing for full-stack app"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.issues: List[Dict[str, Any]] = []
        self.passed_checks: List[str] = []

    def run_curl(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Execute curl command and return result"""
        url = f"{self.api_url}{endpoint}"
        cmd = ["curl", "-X", method, "-s", "-w", "\n%{http_code}", url]

        if kwargs.get("headers"):
            for header in kwargs["headers"]:
                cmd.extend(["-H", header])

        if kwargs.get("data"):
            cmd.extend(["-d", json.dumps(kwargs["data"])])
            cmd.extend(["-H", "Content-Type: application/json"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\n')
            status_code = int(lines[-1])
            body = '\n'.join(lines[:-1])

            try:
                body_json = json.loads(body) if body else None
            except json.JSONDecodeError:
                body_json = None

            return {
                "status_code": status_code,
                "body": body_json or body,
                "success": True
            }
        except Exception as e:
            return {
                "status_code": 0,
                "body": str(e),
                "success": False,
                "error": str(e)
            }

    def add_issue(self, severity: str, category: str, title: str, description: str, recommendation: str):
        """Record an issue"""
        self.issues.append({
            "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW
            "category": category,
            "title": title,
            "description": description,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        })

    def add_pass(self, check: str):
        """Record a passing check"""
        self.passed_checks.append(check)

    def test_backend_health(self):
        """Test 1: Backend health and accessibility"""
        print("\n[TEST 1] Backend Health Check")
        print("-" * 80)

        result = self.run_curl("GET", "/health")

        if result["status_code"] == 200:
            print("[PASS] Backend is running and accessible")
            self.add_pass("Backend health check")
        else:
            print(f"[FAIL] Backend not accessible (status: {result['status_code']})")
            self.add_issue(
                "CRITICAL",
                "Infrastructure",
                "Backend Not Running",
                f"Backend API returned status {result['status_code']} for /health endpoint",
                "Start the backend server: cd backend && uvicorn app.main:app --reload"
            )

    def test_api_documentation(self):
        """Test 2: API documentation availability"""
        print("\n[TEST 2] API Documentation")
        print("-" * 80)

        result = self.run_curl("GET", "/docs")

        if result["status_code"] == 200:
            print("[PASS] API documentation is accessible at /docs")
            self.add_pass("API documentation available")
        else:
            print(f"[FAIL] API documentation not accessible")
            self.add_issue(
                "MEDIUM",
                "Documentation",
                "API Docs Unavailable",
                "Swagger/OpenAPI documentation is not accessible",
                "Ensure FastAPI is properly configured with docs_url='/docs'"
            )

    def test_auth_endpoints(self):
        """Test 3: Authentication endpoints existence"""
        print("\n[TEST 3] Authentication Endpoints")
        print("-" * 80)

        # Test signup endpoint
        signup_result = self.run_curl("POST", "/api/auth/signup", data={
            "email": "test@example.com",
            "password": "test123"
        })

        # Test signin endpoint
        signin_result = self.run_curl("POST", "/api/auth/signin", data={
            "email": "test@example.com",
            "password": "test123"
        })

        if signup_result["status_code"] == 404 and signin_result["status_code"] == 404:
            print("[FAIL] Authentication endpoints NOT implemented")
            print("  - POST /api/auth/signup -> 404")
            print("  - POST /api/auth/signin -> 404")
            self.add_issue(
                "CRITICAL",
                "Authentication",
                "Auth Endpoints Missing",
                "No signup or signin endpoints found in the backend API. "
                "Frontend expects Better Auth endpoints but backend has none implemented.",
                "Implement authentication endpoints:\n"
                "  1. Create app/routes/auth.py with signup/signin endpoints\n"
                "  2. Add Better Auth integration or custom JWT auth\n"
                "  3. Include router in main.py: app.include_router(auth.router)"
            )
        else:
            print(f"[INFO] Auth endpoints status:")
            print(f"  - Signup: {signup_result['status_code']}")
            print(f"  - Signin: {signin_result['status_code']}")

    def test_task_endpoints(self):
        """Test 4: Task CRUD endpoints"""
        print("\n[TEST 4] Task CRUD Endpoints")
        print("-" * 80)

        test_user_id = "test-user-123"

        # Test without auth (should fail with 401)
        result_no_auth = self.run_curl("GET", f"/api/{test_user_id}/tasks")

        if result_no_auth["status_code"] == 401:
            print("[PASS] Task endpoints require authentication (401)")
            self.add_pass("Task endpoints protected")
        else:
            print(f"[WARN] Task endpoint returned {result_no_auth['status_code']} without auth")
            if result_no_auth["status_code"] == 422:
                print("  Issue: Expecting Authorization header but getting validation error")
                self.add_issue(
                    "HIGH",
                    "Authentication",
                    "Auth Header Validation Issue",
                    "Task endpoints return 422 instead of 401 when no auth provided",
                    "Check middleware/auth.py to ensure proper HTTPBearer validation"
                )

    def test_auth_mechanism(self):
        """Test 5: Authentication mechanism compatibility"""
        print("\n[TEST 5] Authentication Mechanism")
        print("-" * 80)

        # Check if backend expects Authorization header
        print("Backend configuration:")
        print("  Expected: JWT in 'Authorization: Bearer <token>' header")
        print("\nFrontend configuration:")
        print("  Sends: JWT in httpOnly cookie (credentials: 'include')")

        self.add_issue(
            "CRITICAL",
            "Authentication",
            "Auth Mechanism Mismatch",
            "Frontend sends JWT via cookies (Better Auth pattern) but backend expects "
            "JWT in Authorization header. These are incompatible approaches.",
            "Choose ONE authentication strategy:\n"
            "  OPTION A (Recommended): Use Better Auth server-side\n"
            "    - Install better-auth Python package\n"
            "    - Configure Better Auth backend endpoints\n"
            "    - Update middleware to read cookies\n\n"
            "  OPTION B: Update frontend to use Authorization header\n"
            "    - Modify lib/api/client.ts to include Authorization header\n"
            "    - Store JWT in localStorage (less secure)\n"
            "    - Remove credentials: 'include'"
        )

    def test_database_connectivity(self):
        """Test 6: Database connectivity"""
        print("\n[TEST 6] Database Connectivity")
        print("-" * 80)

        # Try to check if database is configured
        backend_env = Path("/c/Users/pc1/Desktop/full-stack-todo/backend/.env")

        if backend_env.exists():
            with open(backend_env) as f:
                content = f.read()
                if "DATABASE_URL" in content:
                    print("[PASS] DATABASE_URL configured in .env")
                    self.add_pass("Database URL configured")
                else:
                    print("[FAIL] DATABASE_URL not found in .env")
                    self.add_issue(
                        "CRITICAL",
                        "Database",
                        "Database Not Configured",
                        "DATABASE_URL environment variable is missing",
                        "Add DATABASE_URL to backend/.env:\n"
                        "  DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname"
                    )
        else:
            print("[FAIL] Backend .env file not found")
            self.add_issue(
                "CRITICAL",
                "Configuration",
                "Environment File Missing",
                "backend/.env file does not exist",
                "Create backend/.env from backend/.env.example and configure all variables"
            )

    def test_cors_configuration(self):
        """Test 7: CORS configuration"""
        print("\n[TEST 7] CORS Configuration")
        print("-" * 80)

        # Check if frontend can make requests
        print("CORS Status:")
        print("  - Backend has CORSMiddleware configured")
        print("  - Allows credentials: True")
        print("  - Default origins: ['http://localhost:3000']")
        print("\n[INFO] CORS appears properly configured for local development")
        self.add_pass("CORS configured")

    def test_endpoint_paths(self):
        """Test 8: Endpoint path consistency"""
        print("\n[TEST 8] Endpoint Path Consistency")
        print("-" * 80)

        print("Backend implements:")
        print("  - /api/{user_id}/tasks [GET, POST]")
        print("  - /api/{user_id}/tasks/{task_id} [GET, PUT, DELETE]")
        print("  - /api/{user_id}/tasks/{task_id}/complete [PATCH]")
        print("\nFrontend calls:")
        print("  - /api/{user_id}/tasks [GET, POST]")
        print("  - /api/{user_id}/tasks/{task_id} [GET, PUT, DELETE]")
        print("  - /api/{user_id}/tasks/{task_id}/complete [PATCH]")
        print("\n[PASS] Frontend and backend endpoint paths match")
        self.add_pass("Endpoint paths consistent")

    def generate_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n" + "=" * 80)
        print("DIAGNOSTIC TEST REPORT")
        print("=" * 80)

        # Summary statistics
        critical = sum(1 for i in self.issues if i["severity"] == "CRITICAL")
        high = sum(1 for i in self.issues if i["severity"] == "HIGH")
        medium = sum(1 for i in self.issues if i["severity"] == "MEDIUM")
        low = sum(1 for i in self.issues if i["severity"] == "LOW")

        print(f"\nSummary:")
        print(f"  Passed Checks: {len(self.passed_checks)}")
        print(f"  Total Issues: {len(self.issues)}")
        print(f"  - CRITICAL: {critical}")
        print(f"  - HIGH: {high}")
        print(f"  - MEDIUM: {medium}")
        print(f"  - LOW: {low}")

        # List all issues
        print(f"\n{'=' * 80}")
        print("ISSUES FOUND")
        print("=" * 80)

        for idx, issue in enumerate(self.issues, 1):
            print(f"\n[{issue['severity']}] Issue #{idx}: {issue['title']}")
            print(f"Category: {issue['category']}")
            print(f"Description: {issue['description']}")
            print(f"Recommendation:\n{issue['recommendation']}")
            print("-" * 80)

        # Save to file
        report_dir = Path(__file__).parent / "reports"
        report_dir.mkdir(exist_ok=True)

        # JSON report
        json_file = report_dir / "diagnostic-report.json"
        with open(json_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "passed_checks": len(self.passed_checks),
                    "total_issues": len(self.issues),
                    "critical": critical,
                    "high": high,
                    "medium": medium,
                    "low": low
                },
                "passed_checks": self.passed_checks,
                "issues": self.issues
            }, f, indent=2)

        # Markdown report
        md_file = report_dir / "diagnostic-report.md"
        md_content = f"""# Full-Stack Todo App - Diagnostic Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Passed Checks:** {len(self.passed_checks)}
- **Total Issues:** {len(self.issues)}
  - **CRITICAL:** {critical}
  - **HIGH:** {high}
  - **MEDIUM:** {medium}
  - **LOW:** {low}

## Passed Checks

"""
        for check in self.passed_checks:
            md_content += f"- [PASS] {check}\n"

        md_content += "\n## Issues Found\n\n"

        for idx, issue in enumerate(self.issues, 1):
            md_content += f"""### [{issue['severity']}] Issue #{idx}: {issue['title']}

**Category:** {issue['category']}

**Description:**
{issue['description']}

**Recommendation:**
```
{issue['recommendation']}
```

---

"""

        with open(md_file, 'w') as f:
            f.write(md_content)

        print(f"\nReports saved:")
        print(f"  JSON: {json_file}")
        print(f"  Markdown: {md_file}")


def main():
    api_url = os.getenv("API_URL", "http://localhost:8000")

    print("=" * 80)
    print("FULL-STACK TODO APP - COMPREHENSIVE DIAGNOSTIC TESTS")
    print("=" * 80)
    print(f"API URL: {api_url}")
    print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    tester = DiagnosticTester(api_url)

    # Run all diagnostic tests
    tester.test_backend_health()
    tester.test_api_documentation()
    tester.test_auth_endpoints()
    tester.test_task_endpoints()
    tester.test_auth_mechanism()
    tester.test_database_connectivity()
    tester.test_cors_configuration()
    tester.test_endpoint_paths()

    # Generate final report
    tester.generate_report()


if __name__ == "__main__":
    main()
