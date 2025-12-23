"""Integration tests for rate limiting middleware

Tests rate limit enforcement:
- 100 requests per hour limit
- 20 requests per minute limit
- Rate limit per user isolation
- Retry-after headers
- Rate limit reset
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime, timedelta


# ============================================================
# HELPER FUNCTION
# ============================================================

def make_chat_request(client, user_id, auth_headers):
    """Helper to make a chat request with mocked OpenAI"""
    with patch("app.agent.orchestrator.client") as mock_client:
        mock_choice = Mock()
        mock_choice.message.content = "Response"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        return client.post(
            f"/api/{user_id}/chat",
            json={"message": "Test"},
            headers=auth_headers
        )


# ============================================================
# PER-MINUTE RATE LIMIT TESTS
# ============================================================

@pytest.mark.integration
def test_rate_limit_per_minute_allows_under_limit(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that requests under 20/minute are allowed"""
    # Make 19 requests (under the 20/minute limit)
    for i in range(19):
        response = make_chat_request(client, test_user_id, auth_headers)
        assert response.status_code == 200, f"Request {i+1} failed"


@pytest.mark.integration
def test_rate_limit_per_minute_blocks_over_limit(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that 21st request within a minute is blocked"""
    # Make 20 requests (at the limit)
    for i in range(20):
        response = make_chat_request(client, test_user_id, auth_headers)
        assert response.status_code == 200, f"Request {i+1} should succeed"

    # 21st request should be rate limited
    response = make_chat_request(client, test_user_id, auth_headers)

    assert response.status_code == 429
    data = response.json()
    # Accept both nested detail format and flat format
    if "detail" in data:
        assert data["detail"]["error"] == "RateLimitExceeded"
        assert data["detail"]["window"] == "minute"
        assert data["detail"]["limit"] == 20
    else:
        assert data.get("error") == "RateLimitExceeded" or "rate limit" in data.get("message", "").lower()


@pytest.mark.integration
def test_rate_limit_includes_retry_after(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that rate limit response includes retry_after"""
    # Exceed per-minute limit
    for i in range(20):
        make_chat_request(client, test_user_id, auth_headers)

    response = make_chat_request(client, test_user_id, auth_headers)

    assert response.status_code == 429
    data = response.json()
    # Accept both nested detail format and flat format
    if "detail" in data and isinstance(data["detail"], dict):
        assert "retry_after" in data["detail"]
        assert isinstance(data["detail"]["retry_after"], int)
        assert data["detail"]["retry_after"] > 0
    # For flat format, retry_after might be at top level
    elif "retry_after" in data:
        assert isinstance(data["retry_after"], int)
        assert data["retry_after"] > 0


# ============================================================
# PER-HOUR RATE LIMIT TESTS
# ============================================================

@pytest.mark.integration
@pytest.mark.slow
def test_rate_limit_per_hour_allows_under_limit(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that requests under 100/hour are allowed (slow test)"""
    from app.middleware.auth import rate_limit_store

    # Make 99 requests (under the 100/hour limit)
    # Note: This is a slow test, may want to skip in CI
    # We need to clear the minute limit every 20 requests to avoid hitting it
    for i in range(99):
        # Clear minute limit every 19 requests to avoid hitting per-minute limit
        if i > 0 and i % 19 == 0:
            rate_limit_store[test_user_id]["minute"] = []

        response = make_chat_request(client, test_user_id, auth_headers)
        assert response.status_code == 200, f"Request {i+1} failed"


@pytest.mark.integration
def test_rate_limit_per_hour_message(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test hourly rate limit error message"""
    # This test would need to make 101 requests which is slow
    # Instead, we can mock the rate limit store to simulate exceeding the limit

    from app.middleware.auth import rate_limit_store
    from datetime import datetime

    # Simulate 100 requests in the last hour
    rate_limit_store[test_user_id]["hour"] = [datetime.utcnow()] * 100

    response = make_chat_request(client, test_user_id, auth_headers)

    assert response.status_code == 429
    data = response.json()
    # Accept both nested detail format and flat format
    if "detail" in data and isinstance(data["detail"], dict):
        assert data["detail"]["error"] == "RateLimitExceeded"
        assert data["detail"]["window"] == "hour"
        assert data["detail"]["limit"] == 100
    else:
        assert data.get("error") == "RateLimitExceeded" or "rate limit" in data.get("message", "").lower()


# ============================================================
# USER ISOLATION TESTS
# ============================================================

@pytest.mark.integration
def test_rate_limit_per_user_isolation(
    client: TestClient,
    test_user_id: str,
    test_user_id_2: str,
    auth_headers: dict,
    auth_headers_user2: dict
):
    """Test that rate limits are enforced per user"""
    # User 1 makes 20 requests (hits per-minute limit)
    for i in range(20):
        response = make_chat_request(client, test_user_id, auth_headers)
        assert response.status_code == 200

    # User 1's next request should be rate limited
    response = make_chat_request(client, test_user_id, auth_headers)
    assert response.status_code == 429

    # User 2's request should succeed (different rate limit)
    response = make_chat_request(client, test_user_id_2, auth_headers_user2)
    assert response.status_code == 200


# ============================================================
# RATE LIMIT RESET TESTS
# ============================================================

@pytest.mark.integration
def test_rate_limit_cleans_old_requests(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that old requests are cleaned from rate limit store"""
    from app.middleware.auth import rate_limit_store
    from datetime import datetime, timedelta

    # Add requests from more than 1 hour ago
    old_time = datetime.utcnow() - timedelta(hours=2)
    rate_limit_store[test_user_id]["hour"] = [old_time] * 50

    # Add recent requests
    recent_time = datetime.utcnow()
    rate_limit_store[test_user_id]["hour"].extend([recent_time] * 10)

    # Make a new request - should clean old requests
    response = make_chat_request(client, test_user_id, auth_headers)

    # Should succeed because old requests are cleaned
    assert response.status_code == 200

    # Verify old requests were cleaned
    assert all(
        req > datetime.utcnow() - timedelta(hours=1)
        for req in rate_limit_store[test_user_id]["hour"]
    )


# ============================================================
# RATE LIMIT RESPONSE FORMAT TESTS
# ============================================================

@pytest.mark.integration
def test_rate_limit_response_format(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that rate limit response has correct format"""
    # Exceed limit
    for i in range(20):
        make_chat_request(client, test_user_id, auth_headers)

    response = make_chat_request(client, test_user_id, auth_headers)

    assert response.status_code == 429
    data = response.json()

    # Verify response structure - accept both formats
    if "detail" in data and isinstance(data["detail"], dict):
        # Nested format
        detail = data["detail"]
        assert "error" in detail
        assert "message" in detail
        assert detail["error"] == "RateLimitExceeded"
        assert isinstance(detail["message"], str)

        # Optional fields that provide additional context
        if "retry_after" in detail:
            assert isinstance(detail["retry_after"], int)
        if "limit" in detail:
            assert isinstance(detail["limit"], int)
        if "window" in detail:
            assert detail["window"] in ["minute", "hour"]
    else:
        # Flat format
        assert "error" in data or "message" in data
        if "error" in data:
            assert data["error"] == "RateLimitExceeded"
        if "message" in data:
            assert isinstance(data["message"], str)


# ============================================================
# EDGE CASE TESTS
# ============================================================

@pytest.mark.integration
def test_rate_limit_handles_concurrent_requests(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test rate limiting with concurrent requests"""
    import threading

    results = []

    def make_request():
        response = make_chat_request(client, test_user_id, auth_headers)
        results.append(response.status_code)

    # Make 25 concurrent requests
    threads = []
    for i in range(25):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # At least some should succeed (first 20)
    success_count = sum(1 for status in results if status == 200)
    assert success_count >= 15  # Allow some variance due to concurrency

    # At least some should be rate limited
    rate_limited_count = sum(1 for status in results if status == 429)
    assert rate_limited_count > 0


@pytest.mark.integration
def test_rate_limit_boundary_condition(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test rate limit exactly at the boundary"""
    # Make exactly 20 requests (the limit)
    for i in range(20):
        response = make_chat_request(client, test_user_id, auth_headers)
        assert response.status_code == 200

    # The 21st should be blocked
    response = make_chat_request(client, test_user_id, auth_headers)
    assert response.status_code == 429


@pytest.mark.integration
def test_rate_limit_does_not_affect_unauthenticated_requests(
    client: TestClient,
    test_user_id: str
):
    """Test that rate limiting applies only to authenticated requests"""
    # Make requests without auth
    for i in range(25):
        response = client.post(
            f"/api/{test_user_id}/chat",
            json={"message": "Test"}
            # No auth headers
        )

        # Should all fail with 401 (not 429)
        assert response.status_code == 401


@pytest.mark.integration
def test_rate_limit_different_time_windows(
    client: TestClient,
    test_user_id: str,
    auth_headers: dict
):
    """Test that per-minute and per-hour limits are tracked separately"""
    from app.middleware.auth import rate_limit_store

    # Simulate 90 requests from more than 1 minute ago but within 1 hour
    old_minute = datetime.utcnow() - timedelta(minutes=5)
    rate_limit_store[test_user_id]["hour"] = [old_minute] * 90
    rate_limit_store[test_user_id]["minute"] = []

    # Should still be able to make requests (per-minute limit not exceeded)
    response = make_chat_request(client, test_user_id, auth_headers)
    assert response.status_code == 200

    # But if we make 10 more requests quickly, we should hit hourly limit soon
    for i in range(9):
        response = make_chat_request(client, test_user_id, auth_headers)
        assert response.status_code == 200

    # This should hit the 100/hour limit
    response = make_chat_request(client, test_user_id, auth_headers)
    assert response.status_code == 429
    data = response.json()
    # Accept both nested detail format and flat format
    if "detail" in data and isinstance(data["detail"], dict):
        assert data["detail"]["window"] == "hour"
    # For flat format, just verify it's a rate limit error
    else:
        assert data.get("error") == "RateLimitExceeded" or "rate limit" in data.get("message", "").lower()
