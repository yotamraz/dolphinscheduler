"""
Functional tests for DolphinScheduler authentication.
Tests session-based login and access control (Spring Security 6 behavior).
"""
import requests
import pytest

BASE_URL = "http://localhost:12345/dolphinscheduler"


@pytest.fixture(autouse=True)
def health_check():
    """Confirm the app is reachable before running tests."""
    resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"


@pytest.fixture
def admin_session():
    """Login as admin and return a valid sessionId."""
    resp = requests.post(
        f"{BASE_URL}/login",
        data={"userName": "admin", "userPassword": "dolphinscheduler123"},
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    return data["data"]["sessionId"]


class TestLogin:
    """POST /login — session-based authentication."""

    def test_login_success(self):
        resp = requests.post(
            f"{BASE_URL}/login",
            data={"userName": "admin", "userPassword": "dolphinscheduler123"},
            timeout=10
        )
        assert resp.status_code == 200

    def test_login_returns_success_true(self):
        resp = requests.post(
            f"{BASE_URL}/login",
            data={"userName": "admin", "userPassword": "dolphinscheduler123"},
            timeout=10
        )
        data = resp.json()
        assert data["success"] is True
        assert data["code"] == 0

    def test_login_returns_session_id(self):
        resp = requests.post(
            f"{BASE_URL}/login",
            data={"userName": "admin", "userPassword": "dolphinscheduler123"},
            timeout=10
        )
        data = resp.json()
        assert "sessionId" in data["data"]
        assert len(data["data"]["sessionId"]) > 0

    def test_login_returns_security_config_type(self):
        resp = requests.post(
            f"{BASE_URL}/login",
            data={"userName": "admin", "userPassword": "dolphinscheduler123"},
            timeout=10
        )
        data = resp.json()
        assert data["data"]["securityConfigType"] == "PASSWORD"

    def test_login_wrong_password(self):
        resp = requests.post(
            f"{BASE_URL}/login",
            data={"userName": "admin", "userPassword": "wrongpassword"},
            timeout=10
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["code"] == 10013

    def test_login_nonexistent_user(self):
        resp = requests.post(
            f"{BASE_URL}/login",
            data={"userName": "nonexistentuser", "userPassword": "anypassword"},
            timeout=10
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    def test_login_missing_credentials(self):
        resp = requests.post(
            f"{BASE_URL}/login",
            data={},
            timeout=10
        )
        # Should return an error response (not 401/403)
        assert resp.status_code in (200, 400)
        if resp.status_code == 200:
            data = resp.json()
            assert data["success"] is False


class TestProtectedEndpoints:
    """Verifies protected endpoints require valid session (Spring Security 6)."""

    def test_users_list_without_auth_returns_401(self):
        """Protected endpoint returns 401 without sessionId."""
        resp = requests.get(f"{BASE_URL}/users/list", timeout=10)
        assert resp.status_code == 401

    def test_projects_without_auth_returns_401(self):
        """Projects endpoint returns 401 without sessionId."""
        resp = requests.get(
            f"{BASE_URL}/projects?pageSize=10&pageNo=1",
            timeout=10
        )
        assert resp.status_code == 401

    def test_users_list_with_invalid_session_returns_401(self):
        """Protected endpoint returns 401 with invalid sessionId."""
        resp = requests.get(
            f"{BASE_URL}/users/list",
            headers={"sessionId": "invalid-session-token"},
            timeout=10
        )
        assert resp.status_code == 401

    def test_users_list_with_valid_session(self, admin_session):
        """Protected endpoint accessible with valid sessionId."""
        resp = requests.get(
            f"{BASE_URL}/users/list",
            headers={"sessionId": admin_session},
            timeout=10
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_get_user_info_with_valid_session(self, admin_session):
        """Get current user info with valid session."""
        resp = requests.get(
            f"{BASE_URL}/users/get-user-info",
            headers={"sessionId": admin_session},
            timeout=10
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["userName"] == "admin"
        assert data["data"]["userType"] == "ADMIN_USER"
