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
Shared pytest fixtures and constants for the DolphinScheduler functional test suite.
"""
import requests
import pytest

BASE_URL = "http://localhost:12345/dolphinscheduler"
HEALTH_URL = f"{BASE_URL}/actuator/health"
LOGIN_URL = f"{BASE_URL}/login"
ADMIN_USER = "admin"
ADMIN_PASS = "dolphinscheduler123"


@pytest.fixture(autouse=True)
def app_is_reachable():
    """Confirm the app is reachable before running each test."""
    resp = requests.get(HEALTH_URL, timeout=10)
    assert resp.status_code == 200, f"App is not reachable: {resp.status_code}"


@pytest.fixture(scope="module")
def admin_session():
    """Login as admin and return session ID."""
    resp = requests.post(
        LOGIN_URL,
        data={"userName": ADMIN_USER, "userPassword": ADMIN_PASS},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    assert resp.status_code == 200, f"Login failed with status {resp.status_code}"
    body = resp.json()
    assert body.get("code") == 0, f"Login returned non-zero code: {body}"
    assert "sessionId" in body.get("data", {}), f"No sessionId in login response: {body}"
    return body["data"]["sessionId"]
