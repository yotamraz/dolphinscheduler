"""
Functional tests for DolphinScheduler projects API.
Tests database read operations and project listing.
"""
import requests
import pytest

BASE_URL = "http://localhost:12345/dolphinscheduler"


@pytest.fixture(autouse=True)
def health_check():
    """Confirm the app is reachable before running tests."""
    resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"


@pytest.fixture(scope="module")
def admin_session():
    """Login as admin and return a valid sessionId (module-scoped)."""
    resp = requests.post(
        f"{BASE_URL}/login",
        data={"userName": "admin", "userPassword": "dolphinscheduler123"},
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    return data["data"]["sessionId"]


class TestProjectsList:
    """GET /projects — list projects with pagination."""

    def test_projects_list_returns_200(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/projects?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        assert resp.status_code == 200

    def test_projects_list_success(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/projects?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        assert data["success"] is True
        assert data["code"] == 0

    def test_projects_list_has_data_structure(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/projects?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        assert "data" in data
        page_data = data["data"]
        assert "totalList" in page_data
        assert "total" in page_data
        assert "pageSize" in page_data

    def test_projects_list_pagination_params(self, admin_session):
        """Pagination parameters are reflected in response."""
        resp = requests.get(
            f"{BASE_URL}/projects?pageSize=5&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        assert data["data"]["pageSize"] == 5

    def test_projects_without_auth_returns_401(self):
        resp = requests.get(
            f"{BASE_URL}/projects?pageSize=10&pageNo=1",
            timeout=10
        )
        assert resp.status_code == 401

    def test_project_nonexistent_code(self, admin_session):
        """Non-existent project returns project-not-found error."""
        resp = requests.get(
            f"{BASE_URL}/projects/99999",
            headers={"sessionId": admin_session},
            timeout=10
        )
        # DolphinScheduler returns 200 with an error code in body for not-found resources
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["code"] == 10190  # Project not found code


class TestQueuesList:
    """GET /queues — tests queue listing (service layer)."""

    def test_queues_list_returns_200(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/queues?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        assert resp.status_code == 200

    def test_queues_list_contains_default(self, admin_session):
        """Default queue is present in DB."""
        resp = requests.get(
            f"{BASE_URL}/queues?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        assert data["success"] is True
        queues = data["data"]["totalList"]
        assert len(queues) >= 1
        queue_names = [q["queueName"] for q in queues]
        assert "default" in queue_names


class TestAlertGroupsList:
    """GET /alert-groups — tests alert service layer."""

    def test_alert_groups_returns_200(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/alert-groups?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        assert resp.status_code == 200

    def test_alert_groups_has_default_group(self, admin_session):
        """Default alert group is seeded in H2 database."""
        resp = requests.get(
            f"{BASE_URL}/alert-groups?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        assert data["success"] is True
        groups = data["data"]["totalList"]
        assert len(groups) >= 1
        group_names = [g["groupName"] for g in groups]
        assert any("default" in name.lower() for name in group_names)
