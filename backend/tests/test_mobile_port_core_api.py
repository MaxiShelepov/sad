import uuid


class TestMobilePortCoreApi:
    """Core regression for license, profiles, warmups, and farm endpoints."""

    def test_license_check_autogenerates_subscription(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        response = api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=20)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["subscription"]["hwid"] == hwid
        assert data["subscription"]["trial_used"] is True

    def test_profiles_create_list_and_profile_route(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        license_response = api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=20)
        assert license_response.status_code == 200

        create_payload = {
            "hwid": hwid,
            "name": "TEST_mobile_profile",
            "email": f"TEST_{uuid.uuid4().hex[:8]}@example.com",
            "access_token": "token-1",
            "proxy": "",
            "notes": "created-by-pytest",
            "use_browser": True,
        }
        create_response = api_client.post(f"{base_url}/api/profiles", json=create_payload, timeout=20)
        assert create_response.status_code == 200
        created = create_response.json()
        profile_id = created["id"]

        list_response = api_client.get(f"{base_url}/api/profiles", params={"hwid": hwid}, timeout=20)
        assert list_response.status_code == 200
        listed_profiles = list_response.json()
        matched = [item for item in listed_profiles if item["id"] == profile_id]
        assert len(matched) == 1
        assert matched[0]["name"] == "TEST_mobile_profile"

        details_response = api_client.get(f"{base_url}/api/profiles/{profile_id}", timeout=20)
        assert details_response.status_code == 200
        details = details_response.json()
        assert details["id"] == profile_id
        assert details["fingerprint"]["profile_id"] == profile_id

        # cleanup
        delete_response = api_client.delete(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=20)
        assert delete_response.status_code == 200

    def test_warmup_start_and_list_logs(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        license_response = api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=20)
        assert license_response.status_code == 200

        profile_payload = {
            "hwid": hwid,
            "name": "TEST_warmup_profile",
            "email": f"TEST_{uuid.uuid4().hex[:8]}@example.com",
            "access_token": "token-2",
            "proxy": "",
            "notes": "warmup-test",
            "use_browser": True,
        }
        profile_response = api_client.post(f"{base_url}/api/profiles", json=profile_payload, timeout=20)
        assert profile_response.status_code == 200
        profile_id = profile_response.json()["id"]

        start_payload = {"hwid": hwid, "profile_id": profile_id, "mode": "balanced", "minutes": 1}
        start_response = api_client.post(f"{base_url}/api/warmups/start", json=start_payload, timeout=20)
        assert start_response.status_code == 200
        started_job = start_response.json()
        assert started_job["profile_id"] == profile_id
        assert started_job["status"] in ["pending", "running"]

        list_response = api_client.get(f"{base_url}/api/warmups", params={"hwid": hwid}, timeout=20)
        assert list_response.status_code == 200
        jobs = list_response.json()
        target = [item for item in jobs if item["id"] == started_job["id"]]
        assert len(target) == 1
        assert isinstance(target[0]["logs"], list)

        stop_response = api_client.post(f"{base_url}/api/warmups/{started_job['id']}/stop", timeout=20)
        assert stop_response.status_code == 200

        delete_response = api_client.delete(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=20)
        assert delete_response.status_code == 200

    def test_farm_start_with_two_profiles(self, api_client, base_url):
        hwid = f"ANDROID-TEST-{uuid.uuid4().hex[:10].upper()}"
        license_response = api_client.post(f"{base_url}/api/license/check", json={"hwid": hwid}, timeout=20)
        assert license_response.status_code == 200

        created_profile_ids = []
        for index in range(2):
            payload = {
                "hwid": hwid,
                "name": f"TEST_farm_{index}",
                "email": f"TEST_{uuid.uuid4().hex[:8]}_{index}@example.com",
                "access_token": f"token-{index}",
                "proxy": "",
                "notes": "farm-test",
                "use_browser": True,
            }
            response = api_client.post(f"{base_url}/api/profiles", json=payload, timeout=20)
            assert response.status_code == 200
            created_profile_ids.append(response.json()["id"])

        farm_payload = {
            "hwid": hwid,
            "items": [
                {"profile_id": created_profile_ids[0], "mode": "calm", "minutes": 1},
                {"profile_id": created_profile_ids[1], "mode": "turbo", "minutes": 1},
            ],
        }
        farm_response = api_client.post(f"{base_url}/api/farm/start", json=farm_payload, timeout=20)
        assert farm_response.status_code == 200
        farm_jobs = farm_response.json()
        assert len(farm_jobs) == 2
        assert all(job["group_id"] for job in farm_jobs)

        stop_farm_response = api_client.post(f"{base_url}/api/farm/stop", params={"hwid": hwid}, timeout=20)
        assert stop_farm_response.status_code == 200
        stopped_payload = stop_farm_response.json()
        assert stopped_payload["success"] is True

        for profile_id in created_profile_ids:
            delete_response = api_client.delete(f"{base_url}/api/profiles/{profile_id}", params={"hwid": hwid}, timeout=20)
            assert delete_response.status_code == 200
