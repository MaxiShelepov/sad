import time
import uuid

import pytest


def _request_with_retry(request_fn, retries: int = 1):
    last_exc = None
    for _ in range(retries + 1):
        try:
            return request_fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(0.4)
    raise last_exc


def _create_profile(api_client, base_url, hwid: str, suffix: str = "core") -> str:
    payload = {
        "hwid": hwid,
        "name": f"TEST_{suffix}_profile",
        "email": f"TEST_{suffix}_{uuid.uuid4().hex[:8]}@example.com",
        "access_token": f"token-{suffix}",
        "proxy": "",
        "notes": "pytest-created",
        "use_browser": True,
    }
    response = _request_with_retry(lambda: api_client.post(f"{base_url}/api/profiles", json=payload, timeout=25))
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == payload["name"]
    return data["id"]


class TestMobilePortCoreApi:
    """Regression for real PHP proxy endpoints and warmup runtime integration."""

    # license module checks
    def test_license_check_autogenerates_subscription(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        response = _request_with_retry(lambda: api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=25))
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["subscription"]["hwid"] == hwid
        assert isinstance(data["subscription"]["active"], bool)

    # dashboard proxy stability and controlled upstream error handling checks
    def test_dashboard_repeated_calls_do_not_return_traceback_500(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        _request_with_retry(lambda: api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=25))

        for _ in range(5):
            response = api_client.get(f"{base_url}/api/dashboard", params={"hwid": hwid}, timeout=25)
            assert response.status_code in {200, 502}
            data = response.json()

            if response.status_code == 200:
                assert isinstance(data.get("profiles_total"), int)
                assert isinstance(data.get("profiles_running"), int)
                assert isinstance(data.get("active_jobs"), int)
            else:
                assert data.get("success") is False
                assert isinstance(data.get("detail"), str)

    # profile CRUD module checks
    def test_profiles_create_list_detail_and_delete(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        _request_with_retry(lambda: api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=25))

        profile_id = _create_profile(api_client, base_url, hwid, "crud")
        try:
            list_response = _request_with_retry(lambda: api_client.get(f"{base_url}/api/profiles", params={"hwid": hwid}, timeout=25))
            assert list_response.status_code == 200
            listed = list_response.json()
            assert any(item["id"] == profile_id for item in listed)

            details_response = _request_with_retry(
                lambda: api_client.get(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=25)
            )
            assert details_response.status_code == 200
            details = details_response.json()
            assert details["id"] == profile_id
            assert details["fingerprint"]["profile_id"] == profile_id
        finally:
            delete_response = api_client.delete(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=25)
            assert delete_response.status_code == 200
            verify_deleted = api_client.get(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=25)
            assert verify_deleted.status_code == 404

    # fingerprint module checks
    def test_fingerprint_get_update_randomize(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        _request_with_retry(lambda: api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=25))

        profile_id = _create_profile(api_client, base_url, hwid, "fp")
        try:
            get_fp = api_client.get(f"{base_url}/api/profiles/{profile_id}/fingerprint", params={"hwid": hwid}, timeout=25)
            assert get_fp.status_code == 200
            current = get_fp.json()["fingerprint"]
            assert current["profile_id"] == profile_id

            update_payload = {
                "browser": "Chrome Mobile",
                "browser_version": "128.0.0.0",
                "os_name": "Android",
                "screen_width": 412,
                "screen_height": 915,
                "timezone": "Europe/Moscow",
            }
            update_response = api_client.put(
                f"{base_url}/api/profiles/{profile_id}/fingerprint", params={"hwid": hwid}, json=update_payload, timeout=25
            )
            assert update_response.status_code == 200

            verify_updated = api_client.get(f"{base_url}/api/profiles/{profile_id}/fingerprint", params={"hwid": hwid}, timeout=25)
            assert verify_updated.status_code == 200
            verified = verify_updated.json()["fingerprint"]
            assert verified["screen_width"] == 412

            randomize_response = api_client.post(
                f"{base_url}/api/profiles/{profile_id}/fingerprint/randomize", params={"hwid": hwid}, timeout=25
            )
            assert randomize_response.status_code == 200
            randomized = randomize_response.json()
            assert randomized["id"] == profile_id
        finally:
            cleanup = api_client.delete(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=25)
            assert cleanup.status_code == 200

    # session module checks
    def test_session_get_and_update(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        _request_with_retry(lambda: api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=25))

        profile_id = _create_profile(api_client, base_url, hwid, "session")
        try:
            update_payload = {"cookies": [{"name": "sid", "value": "abc123"}], "meta": {"source": "pytest"}}
            update_response = api_client.put(
                f"{base_url}/api/profiles/{profile_id}/session", params={"hwid": hwid}, json={"data": update_payload}, timeout=25
            )
            assert update_response.status_code == 200

            get_response = api_client.get(f"{base_url}/api/profiles/{profile_id}/session", params={"hwid": hwid}, timeout=25)
            assert get_response.status_code == 200
            restored = get_response.json()["session_data"]
            assert restored["cookies"][0]["name"] == "sid"
        finally:
            cleanup = api_client.delete(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=25)
            assert cleanup.status_code == 200

    # warmup runtime and reflected metrics module checks
    def test_warmup_start_stop_and_profile_metrics(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        _request_with_retry(lambda: api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=25))

        profile_id = _create_profile(api_client, base_url, hwid, "warmup")
        started_job_id = None
        try:
            start_payload = {"hwid": hwid, "profile_id": profile_id, "mode": "balanced", "minutes": 1}
            start_response = api_client.post(f"{base_url}/api/warmups/start", json=start_payload, timeout=25)
            assert start_response.status_code == 200
            started_job = start_response.json()
            started_job_id = started_job["id"]
            assert started_job["profile_id"] == profile_id

            time.sleep(3)
            list_response = api_client.get(f"{base_url}/api/warmups", params={"hwid": hwid}, timeout=25)
            assert list_response.status_code == 200
            jobs = list_response.json()
            current = next((item for item in jobs if item["id"] == started_job_id), None)
            assert current is not None

            detail_response = api_client.get(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=25)
            assert detail_response.status_code == 200
            detail = detail_response.json()
            assert isinstance(detail["stats"]["trust_score"], int)
            assert isinstance(detail["stats"]["total_operations"], int)
        finally:
            if started_job_id:
                stop_response = api_client.post(f"{base_url}/api/warmups/{started_job_id}/stop", timeout=25)
                assert stop_response.status_code == 200
            cleanup = api_client.delete(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=25)
            assert cleanup.status_code == 200

    # farm module checks
    def test_farm_start_and_stop(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        license_response = _request_with_retry(lambda: api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=25))
        assert license_response.status_code == 200

        created_ids = [_create_profile(api_client, base_url, hwid, f"farm_{idx}") for idx in range(2)]
        try:
            farm_payload = {
                "hwid": hwid,
                "items": [
                    {"profile_id": created_ids[0], "mode": "calm", "minutes": 1},
                    {"profile_id": created_ids[1], "mode": "turbo", "minutes": 1},
                ],
            }
            farm_response = api_client.post(f"{base_url}/api/farm/start", json=farm_payload, timeout=25)
            if farm_response.status_code == 403:
                pytest.skip("Farm mode disabled for current subscription plan")

            assert farm_response.status_code == 200
            farm_jobs = farm_response.json()
            assert len(farm_jobs) >= 1

            stop_response = api_client.post(f"{base_url}/api/farm/stop", params={"hwid": hwid}, timeout=25)
            assert stop_response.status_code == 200
            assert stop_response.json()["success"] is True
        finally:
            for profile_id in created_ids:
                cleanup = api_client.delete(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=25)
                assert cleanup.status_code == 200
