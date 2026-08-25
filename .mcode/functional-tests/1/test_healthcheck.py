"""
Functional tests for DolphinScheduler Standalone Server health endpoint.
Verifies that all 5 components (api, master, worker, alert, db) report UP.
"""
import requests
import pytest

BASE_URL = "http://localhost:12345/dolphinscheduler"
HEALTH_URL = f"{BASE_URL}/actuator/health"


@pytest.fixture(autouse=True)
def app_is_reachable():
    """Confirm the app is reachable before running tests."""
    resp = requests.get(HEALTH_URL, timeout=10)
    assert resp.status_code == 200, f"App is not reachable: {resp.status_code}"


class TestHealthcheckEndpoint:
    """GET /actuator/health — Spring Boot health endpoint."""

    def test_health_returns_200(self):
        resp = requests.get(HEALTH_URL, timeout=10)
        assert resp.status_code == 200

    def test_health_status_is_up(self):
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        assert body["status"] == "UP", f"Overall status not UP: {body}"

    def test_health_api_component_up(self):
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        components = body.get("components", {})
        assert "api" in components, "api component missing from health response"
        assert components["api"]["status"] == "UP", f"api not UP: {components['api']}"

    def test_health_master_component_up(self):
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        components = body.get("components", {})
        assert "master" in components, "master component missing from health response"
        assert components["master"]["status"] == "UP", f"master not UP: {components['master']}"

    def test_health_worker_component_up(self):
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        components = body.get("components", {})
        assert "worker" in components, "worker component missing from health response"
        assert components["worker"]["status"] == "UP", f"worker not UP: {components['worker']}"

    def test_health_alert_component_up(self):
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        components = body.get("components", {})
        assert "alert" in components, "alert component missing from health response"
        assert components["alert"]["status"] == "UP", f"alert not UP: {components['alert']}"

    def test_health_db_component_up(self):
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        components = body.get("components", {})
        assert "db" in components, "db component missing from health response"
        assert components["db"]["status"] == "UP", f"db not UP: {components['db']}"

    def test_health_db_is_h2(self):
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        db_details = body.get("components", {}).get("db", {}).get("details", {})
        assert db_details.get("database") == "H2", f"Expected H2 database, got: {db_details}"

    def test_health_no_auth_required(self):
        """Actuator health must be accessible without authentication."""
        resp = requests.get(HEALTH_URL, timeout=10)
        # Must not return 401 or 403
        assert resp.status_code not in (401, 403), \
            f"Health endpoint requires auth (status {resp.status_code})"

    def test_health_all_five_components_present(self):
        """All 5 expected service components are present and UP in the health response."""
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        components = body.get("components", {})
        expected = ["api", "master", "worker", "alert", "db"]
        for comp in expected:
            assert comp in components, f"Component '{comp}' missing from health"
            assert components[comp]["status"] == "UP", \
                f"Component '{comp}' not UP: {components[comp]}"
