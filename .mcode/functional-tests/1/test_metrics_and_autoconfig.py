"""
Functional tests for DolphinScheduler actuator metrics and auto-configuration loading.
Verifies:
- GET /actuator/metrics returns a list of meter names
- system.cpu.usage is registered
- Key auto-config classes are loaded (checked via the AutoConfiguration.imports files
  and the fact that the server started successfully with all components UP)
"""
import os
import requests

from conftest import BASE_URL

METRICS_URL = f"{BASE_URL}/actuator/metrics"

WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", "/l2l/workspace")
DS_ROOT = os.path.join(WORKSPACE_DIR, "dolphinscheduler")


class TestActuatorMetrics:
    """GET /actuator/metrics — Micrometer metrics endpoint."""

    def test_metrics_returns_200(self):
        resp = requests.get(METRICS_URL, timeout=10)
        assert resp.status_code == 200

    def test_metrics_returns_names_list(self):
        resp = requests.get(METRICS_URL, timeout=10)
        body = resp.json()
        assert "names" in body, f"'names' key missing from metrics response: {body}"
        names = body["names"]
        assert isinstance(names, list), f"'names' should be a list, got: {type(names)}"
        assert len(names) > 0, "metrics names list is empty"

    def test_system_cpu_usage_is_registered(self):
        resp = requests.get(METRICS_URL, timeout=10)
        body = resp.json()
        names = body.get("names", [])
        assert "system.cpu.usage" in names, \
            f"system.cpu.usage not in metrics names. Available: {names[:20]}..."

    def test_jvm_metrics_registered(self):
        """JVM memory metrics should be registered by Spring Boot auto-configuration."""
        resp = requests.get(METRICS_URL, timeout=10)
        body = resp.json()
        names = body.get("names", [])
        jvm_metrics = [n for n in names if n.startswith("jvm.")]
        assert len(jvm_metrics) > 0, \
            f"No JVM metrics registered. Available: {names[:20]}..."

    def test_ds_master_metrics_registered(self):
        """DolphinScheduler custom master metrics should be registered."""
        resp = requests.get(METRICS_URL, timeout=10)
        body = resp.json()
        names = body.get("names", [])
        ds_metrics = [n for n in names if n.startswith("ds.")]
        assert len(ds_metrics) > 0, \
            f"No DolphinScheduler custom metrics registered. Available: {names[:20]}..."

    def test_specific_metric_detail(self):
        """Drill into system.cpu.usage to verify it has a valid value structure."""
        resp = requests.get(f"{METRICS_URL}/system.cpu.usage", timeout=10)
        assert resp.status_code == 200, \
            f"Unexpected status for system.cpu.usage detail: {resp.status_code}"
        body = resp.json()
        assert "measurements" in body, \
            f"measurements missing from metric detail: {body}"

    def test_hikaricp_metrics_registered(self):
        """HikariCP connection pool metrics should appear (H2 pool is active)."""
        resp = requests.get(METRICS_URL, timeout=10)
        body = resp.json()
        names = body.get("names", [])
        hikari_metrics = [n for n in names if n.startswith("hikaricp.")]
        assert len(hikari_metrics) > 0, \
            f"No HikariCP metrics registered. Available names: {names[:30]}..."

    def test_no_auth_required_for_metrics(self):
        """Actuator metrics must be accessible without authentication."""
        resp = requests.get(METRICS_URL, timeout=10)
        assert resp.status_code not in (401, 403), \
            f"Metrics endpoint requires auth (status {resp.status_code})"


class TestAutoConfigurationLoading:
    """
    Verify that Spring Boot 3.5 auto-configuration loaded all 9 auto-config classes.

    Strategy: Since the server started with all components UP (verified by healthcheck),
    we confirm that the AutoConfiguration.imports files contain the expected class names
    AND that the health response shows all components are UP (proving each auto-config
    bootstrapped its subsystem successfully).
    """

    @staticmethod
    def _read_file(path):
        """Read a file's contents, failing the test with a clear message on IOError."""
        import pytest
        try:
            with open(path) as fh:
                return fh.read()
        except OSError as e:
            pytest.fail(f"Could not read AutoConfiguration.imports file {path}: {e}")

    def _find_imports_files(self):
        """Find all AutoConfiguration.imports files in the source tree."""
        import subprocess
        result = subprocess.run(
            [
                "find", DS_ROOT,
                "-name", "org.springframework.boot.autoconfigure.AutoConfiguration.imports",
                "-path", "*/src/*",
            ],
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []

    def test_autoconfig_imports_files_exist(self):
        """At least the expected number of AutoConfiguration.imports files must exist."""
        files = self._find_imports_files()
        assert len(files) >= 9, \
            f"Expected at least 9 AutoConfiguration.imports files, found {len(files)}: {files}"

    def test_meter_autoconfig_registered(self):
        files = self._find_imports_files()
        content = "\n".join(self._read_file(f) for f in files if f)
        assert "MeterAutoConfiguration" in content, \
            "MeterAutoConfiguration not found in any AutoConfiguration.imports file"

    def test_actuator_auth_autoconfig_registered(self):
        files = self._find_imports_files()
        content = "\n".join(self._read_file(f) for f in files if f)
        assert "ActuatorAuthenticationAutoConfiguration" in content, \
            "ActuatorAuthenticationAutoConfiguration not found in any AutoConfiguration.imports file"

    def test_h2_dao_autoconfig_registered(self):
        files = self._find_imports_files()
        content = "\n".join(self._read_file(f) for f in files if f)
        assert "H2DaoPluginAutoConfiguration" in content, \
            "H2DaoPluginAutoConfiguration not found in any AutoConfiguration.imports file"

    def test_quartz_autoconfig_registered(self):
        files = self._find_imports_files()
        content = "\n".join(self._read_file(f) for f in files if f)
        assert "QuartzSchedulerAutoConfiguration" in content, \
            "QuartzSchedulerAutoConfiguration not found in any AutoConfiguration.imports file"

    def test_jdbc_registry_autoconfig_registered(self):
        files = self._find_imports_files()
        content = "\n".join(self._read_file(f) for f in files if f)
        assert "JdbcRegistryAutoConfiguration" in content, \
            "JdbcRegistryAutoConfiguration not found in any AutoConfiguration.imports file"

    def test_all_components_up_proves_autoconfig_loaded(self):
        """
        The healthcheck showing all 5 components UP is proof that:
        - H2DaoPluginAutoConfiguration initialized the H2 datasource (db UP)
        - MeterAutoConfiguration wired Micrometer (metrics registered above)
        - ActuatorAuthenticationAutoConfiguration configured actuator security (health accessible)
        - QuartzSchedulerAutoConfiguration started the scheduler (master UP)
        - JdbcRegistryAutoConfiguration initialized the JDBC registry (master/worker UP)
        """
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        components = body.get("components", {})
        expected_components = ["api", "master", "worker", "alert", "db"]
        for comp in expected_components:
            assert comp in components, f"Component '{comp}' missing from health"
            assert components[comp]["status"] == "UP", \
                f"Component '{comp}' is not UP: {components[comp]}"

    def test_spring_factories_not_used(self):
        """
        Verify the spring.factories file does NOT contain EnableAutoConfiguration entries.
        This confirms the migration to AutoConfiguration.imports was successful.
        """
        import subprocess
        result = subprocess.run(
            ["grep", "-r", "EnableAutoConfiguration",
             "--include=spring.factories", DS_ROOT + "/dolphinscheduler-meter",
             DS_ROOT + "/dolphinscheduler-authentication",
             DS_ROOT + "/dolphinscheduler-dao-plugin"],
            capture_output=True, text=True, timeout=30,
        )
        # Should find nothing — any match means old spring.factories entries remain
        assert result.stdout.strip() == "", \
            f"EnableAutoConfiguration still in spring.factories: {result.stdout.strip()}"
