"""
Functional tests for DolphinScheduler actuator health endpoints.
Tests that all server components (api, master, worker, alert, db) are UP.
"""
import requests
import pytest

BASE_URL = "http://localhost:12345/dolphinscheduler"


@pytest.fixture(autouse=True)
def health_check():
    """Confirm the app is reachable before running tests."""
    resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"


class TestActuatorHealth:
    """GET /actuator/health — verifies server startup and all component health."""

    def test_health_returns_200(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        assert resp.status_code == 200

    def test_health_status_is_up(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        data = resp.json()
        assert data["status"] == "UP"

    def test_health_has_components(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        data = resp.json()
        assert "components" in data

    def test_health_api_component_up(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        data = resp.json()
        assert data["components"]["api"]["status"] == "UP"

    def test_health_master_component_up(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        data = resp.json()
        assert data["components"]["master"]["status"] == "UP"

    def test_health_worker_component_up(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        data = resp.json()
        assert data["components"]["worker"]["status"] == "UP"

    def test_health_alert_component_up(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        data = resp.json()
        assert data["components"]["alert"]["status"] == "UP"

    def test_health_db_component_up(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        data = resp.json()
        assert data["components"]["db"]["status"] == "UP"

    def test_health_db_is_h2(self):
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        data = resp.json()
        assert data["components"]["db"]["details"]["database"] == "H2"

    def test_health_unauthenticated(self):
        """Actuator health should be accessible without authentication."""
        resp = requests.get(f"{BASE_URL}/actuator/health", timeout=10)
        assert resp.status_code == 200

    def test_health_no_session_header(self):
        """Health endpoint should not require sessionId."""
        resp = requests.get(
            f"{BASE_URL}/actuator/health",
            headers={},
            timeout=10
        )
        assert resp.status_code == 200


class TestActuatorPrometheus:
    """GET /actuator/prometheus — verifies metrics endpoint accessibility."""

    def test_prometheus_returns_200(self):
        """Prometheus metrics endpoint should be accessible."""
        resp = requests.get(f"{BASE_URL}/actuator/prometheus", timeout=10)
        assert resp.status_code == 200

    def test_prometheus_unauthenticated(self):
        """Prometheus endpoint should be accessible without authentication (Spring Security 6 config)."""
        resp = requests.get(
            f"{BASE_URL}/actuator/prometheus",
            headers={},
            timeout=10
        )
        assert resp.status_code == 200
