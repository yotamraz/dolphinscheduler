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
Functional tests for DolphinScheduler REST API authentication.
Covers login, session-based API calls, and auth enforcement.
"""
import requests

from conftest import BASE_URL, LOGIN_URL, ADMIN_USER, ADMIN_PASS


class TestLogin:
    """POST /login — authentication endpoint."""

    def test_login_success(self):
        resp = requests.post(
            LOGIN_URL,
            data={"userName": ADMIN_USER, "userPassword": ADMIN_PASS},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        assert resp.status_code == 200

    def test_login_returns_session_id(self):
        resp = requests.post(
            LOGIN_URL,
            data={"userName": ADMIN_USER, "userPassword": ADMIN_PASS},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        body = resp.json()
        assert body.get("code") == 0, f"Expected code 0, got: {body}"
        assert "sessionId" in body.get("data", {}), f"No sessionId in data: {body}"
        session_id = body["data"]["sessionId"]
        assert len(session_id) > 0, "sessionId is empty"

    def test_login_wrong_password(self):
        resp = requests.post(
            LOGIN_URL,
            data={"userName": ADMIN_USER, "userPassword": "wrong_password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        # Either 200 with non-zero code or a 4xx error
        if resp.status_code == 200:
            body = resp.json()
            assert body.get("code") != 0, \
                f"Login with wrong password should not return code 0: {body}"
        else:
            assert resp.status_code in (400, 401, 403), \
                f"Unexpected status for wrong password: {resp.status_code}"

    def test_login_missing_credentials(self):
        resp = requests.post(
            LOGIN_URL,
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        # Should not succeed
        if resp.status_code == 200:
            body = resp.json()
            assert body.get("code") != 0, \
                f"Login with no credentials should not return code 0: {body}"
        else:
            assert resp.status_code >= 400, \
                f"Expected error for missing credentials, got: {resp.status_code}"

    def test_login_success_indicator(self):
        resp = requests.post(
            LOGIN_URL,
            data={"userName": ADMIN_USER, "userPassword": ADMIN_PASS},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        body = resp.json()
        assert body.get("success") is True, f"success field not True: {body}"


class TestAuthEnforcement:
    """Verify that protected endpoints require authentication."""

    def test_projects_endpoint_requires_auth(self):
        resp = requests.get(
            f"{BASE_URL}/projects?pageNo=1&pageSize=10",
            timeout=10,
        )
        assert resp.status_code == 401, \
            f"Expected 401 for unauthenticated /projects, got {resp.status_code}"

    def test_users_list_requires_auth(self):
        resp = requests.get(
            f"{BASE_URL}/users/list",
            timeout=10,
        )
        assert resp.status_code == 401, \
            f"Expected 401 for unauthenticated /users/list, got {resp.status_code}"


class TestSessionAuthentication:
    """Test authenticated API calls using session cookie."""

    def test_authenticated_users_list(self, admin_session):
        """GET /users/list returns non-admin users (success code 0, list structure)."""
        resp = requests.get(
            f"{BASE_URL}/users/list",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        assert resp.status_code == 200, \
            f"Authenticated /users/list returned {resp.status_code}"
        body = resp.json()
        assert body.get("code") == 0, f"Expected code 0: {body}"
        # data is a list (possibly empty if only admin exists)
        assert isinstance(body.get("data"), list), \
            f"Expected list for data field: {body.get('data')}"

    def test_authenticated_users_list_paging_returns_admin(self, admin_session):
        """GET /users/list-paging includes admin user in totalList."""
        resp = requests.get(
            f"{BASE_URL}/users/list-paging?pageNo=1&pageSize=10",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        body = resp.json()
        assert body.get("code") == 0, f"Expected code 0, got: {body}"
        total_list = body.get("data", {}).get("totalList", [])
        user_names = [u.get("userName") for u in total_list]
        assert "admin" in user_names, f"admin not found in paging list: {total_list}"

    def test_authenticated_users_list_paging(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/users/list-paging?pageNo=1&pageSize=10",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        assert resp.status_code == 200, \
            f"Authenticated /users/list-paging returned {resp.status_code}"
        body = resp.json()
        assert body.get("code") == 0, f"Expected code 0, got: {body}"
        data = body.get("data", {})
        assert "totalList" in data, f"totalList missing from paging response: {data}"

    def test_authenticated_projects_list(self, admin_session):
        resp = requests.get(
            f"{BASE_URL}/projects?pageNo=1&pageSize=10&searchVal=",
            headers={"Cookie": f"sessionId={admin_session}"},
            timeout=10,
        )
        assert resp.status_code == 200, \
            f"Authenticated /projects returned {resp.status_code}"
        body = resp.json()
        assert body.get("code") == 0, f"Expected code 0 on projects list: {body}"

    def test_invalid_session_is_rejected(self):
        resp = requests.get(
            f"{BASE_URL}/users/list",
            headers={"Cookie": "sessionId=invalid-session-id-xyz"},
            timeout=10,
        )
        assert resp.status_code in (401, 403), \
            f"Expected 401/403 for invalid session, got {resp.status_code}"
