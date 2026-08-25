"""
Functional tests for DolphinScheduler tenants API.
Tests the database layer through tenant CRUD operations.
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


class TestTenantsList:
    """GET /tenants — list tenants with pagination."""

    def test_tenants_list_returns_200(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/tenants?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        assert resp.status_code == 200

    def test_tenants_list_success(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/tenants?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        assert data["success"] is True
        assert data["code"] == 0

    def test_tenants_list_has_data(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/tenants?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        assert "data" in data
        assert "totalList" in data["data"]

    def test_tenants_list_contains_default_tenant(self, admin_session):
        """DB layer works: default tenant seeded by H2 schema init is readable."""
        resp = requests.get(
            f"{BASE_URL}/tenants?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        tenants = data["data"]["totalList"]
        assert len(tenants) >= 1
        tenant_codes = [t["tenantCode"] for t in tenants]
        assert "default" in tenant_codes

    def test_tenants_list_default_tenant_structure(self, admin_session):
        """Default tenant has expected fields."""
        resp = requests.get(
            f"{BASE_URL}/tenants?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        tenants = data["data"]["totalList"]
        default_tenant = next(t for t in tenants if t["tenantCode"] == "default")
        assert default_tenant["id"] == -1
        assert default_tenant["description"] == "default tenant"

    def test_tenants_list_all_returns_200(self, admin_session):
        """GET /tenants/list returns all tenants (non-paginated)."""
        resp = requests.get(
            f"{BASE_URL}/tenants/list",
            headers={"sessionId": admin_session},
            timeout=10
        )
        assert resp.status_code == 200

    def test_tenants_list_all_success(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/tenants/list",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    def test_tenants_without_auth_returns_401(self):
        resp = requests.get(
            f"{BASE_URL}/tenants?pageSize=10&pageNo=1",
            timeout=10
        )
        assert resp.status_code == 401

    def test_tenants_pagination_structure(self, admin_session):
        """Pagination metadata is present and correctly structured."""
        resp = requests.get(
            f"{BASE_URL}/tenants?pageSize=10&pageNo=1",
            headers={"sessionId": admin_session},
            timeout=10
        )
        data = resp.json()
        page_data = data["data"]
        assert "total" in page_data
        assert "totalPage" in page_data
        assert "pageSize" in page_data
        assert page_data["pageSize"] == 10
