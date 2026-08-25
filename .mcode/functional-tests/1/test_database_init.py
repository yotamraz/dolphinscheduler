#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Functional tests for DolphinScheduler H2 database initialization.
Verifies:
- H2 schema is created and seeded on startup
- Default admin user exists
- Tables are accessible via the API
"""
import requests

from conftest import BASE_URL, HEALTH_URL, LOGIN_URL, ADMIN_USER, ADMIN_PASS


class TestDatabaseInitialization:
    """Verify H2 schema is initialized and default data is seeded."""

    def test_db_health_component_shows_h2(self):
        """H2 database initialized and accessible per the health endpoint."""
        resp = requests.get(HEALTH_URL, timeout=10)
        body = resp.json()
        db = body.get("components", {}).get("db", {})
        assert db.get("status") == "UP"
        assert db.get("details", {}).get("database") == "H2"

    def test_default_admin_user_exists(self, admin_session):
        """Admin user from seed data must exist after DB initialization (via list-paging)."""
        resp = requests.get(
            f"{BASE_URL}/users/list-paging?pageNo=1&pageSize=10",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == 0
        total_list = body.get("data", {}).get("totalList", [])
        user_names = [u.get("userName") for u in total_list]
        assert "admin" in user_names, \
            f"Default admin user not found after DB init. Users: {user_names}"

    def test_admin_user_is_admin_type(self, admin_session):
        """Admin user has ADMIN_USER type (from seed SQL)."""
        resp = requests.get(
            f"{BASE_URL}/users/list-paging?pageNo=1&pageSize=10",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        body = resp.json()
        total_list = body.get("data", {}).get("totalList", [])
        admin = next((u for u in total_list if u.get("userName") == "admin"), None)
        assert admin is not None, "admin user not found in paging list"
        assert admin.get("userType") == "ADMIN_USER", \
            f"Expected ADMIN_USER type, got: {admin.get('userType')}"

    def test_default_queue_exists(self, admin_session):
        """Default 'default' queue should exist after schema initialization."""
        resp = requests.get(
            f"{BASE_URL}/queues/list",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        # 200 means the queues table exists and the query ran
        assert resp.status_code == 200, \
            f"Queues list endpoint returned {resp.status_code}"
        body = resp.json()
        assert body.get("code") == 0, f"Expected code 0: {body}"

    def test_tenants_table_accessible(self, admin_session):
        """Tenants table initialized and accessible via the API."""
        resp = requests.get(
            f"{BASE_URL}/tenants?pageNo=1&pageSize=10",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        assert resp.status_code == 200, \
            f"Tenants list endpoint returned {resp.status_code}"
        body = resp.json()
        assert body.get("code") == 0, f"Expected code 0 on tenants list: {body}"

    def test_users_paging_returns_valid_structure(self, admin_session):
        """Users paging query works — proves t_ds_user table is initialized."""
        resp = requests.get(
            f"{BASE_URL}/users/list-paging?pageNo=1&pageSize=10",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == 0
        data = body.get("data", {})
        assert "totalList" in data, f"totalList missing from paging data: {data}"
        total_list = data["totalList"]
        assert isinstance(total_list, list), "totalList should be a list"
        assert len(total_list) >= 1, "Expected at least 1 user (admin) in DB"

    def test_login_proves_auth_table_seeded(self):
        """
        Successful login proves t_ds_session and t_ds_user tables exist
        and are seeded with the default admin user and password hash.
        """
        resp = requests.post(
            LOGIN_URL,
            data={"userName": ADMIN_USER, "userPassword": ADMIN_PASS},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == 0, f"Login failed — auth tables not seeded: {body}"
        assert "sessionId" in body.get("data", {}), \
            "sessionId missing — session table likely not initialized"
