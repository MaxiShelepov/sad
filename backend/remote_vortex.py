from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env.custom', override=True)

API_URL = os.getenv('VORTEX_API_URL', 'https://e-vortex.ru/api.php')
API_KEY = os.getenv('VORTEX_API_KEY', '')


class VortexRemoteError(RuntimeError):
    pass


def _request(action: str, payload: dict[str, Any] | None = None, with_api_key: bool = False) -> dict[str, Any]:
    form_data = {'action': action, **(payload or {})}
    if with_api_key:
        form_data['api_key'] = API_KEY

    response = requests.post(API_URL, data=form_data, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not data.get('success'):
        raise VortexRemoteError(data.get('error') or data.get('message') or f'API action failed: {action}')
    return data


def ping() -> dict[str, Any]:
    return _request('ping')


def check_hwid(hwid: str) -> dict[str, Any]:
    return _request('check_hwid', {'hwid': hwid})


def get_profiles(hwid: str) -> dict[str, Any]:
    return _request('get_profiles', {'hwid': hwid})


def create_profile(hwid: str, email: str, access_token: str, proxy: str = '', name: str = '', use_browser: bool = True) -> dict[str, Any]:
    return _request(
        'create_profile',
        {
            'hwid': hwid,
            'email': email,
            'access_token': access_token,
            'proxy': proxy,
            'name': name,
            'use_browser': 1 if use_browser else 0,
        },
    )


def update_profile(hwid: str, profile_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    return _request('update_profile', {'hwid': hwid, 'profile_id': profile_id, **updates})


def delete_profile(hwid: str, profile_id: str) -> dict[str, Any]:
    return _request('delete_profile', {'hwid': hwid, 'profile_id': profile_id})


def load_fingerprint(hwid: str, profile_id: str) -> dict[str, Any]:
    return _request('load_fingerprint', {'hwid': hwid, 'profile_id': profile_id})


def save_fingerprint(hwid: str, profile_id: str, fingerprint: dict[str, Any]) -> dict[str, Any]:
    return _request('save_fingerprint', {'hwid': hwid, 'profile_id': profile_id, 'fp_data': json.dumps(fingerprint)})


def load_session(hwid: str, profile_id: str) -> dict[str, Any]:
    return _request('load_session', {'hwid': hwid, 'profile_id': profile_id}, with_api_key=True)


def save_session(hwid: str, profile_id: str, session_data: dict[str, Any]) -> dict[str, Any]:
    return _request(
        'save_session',
        {'hwid': hwid, 'profile_id': profile_id, 'session_data': json.dumps(session_data)},
        with_api_key=True,
    )


def add_operation(hwid: str, profile_id: str, success: bool, action_text: str) -> dict[str, Any]:
    return _request(
        'add_operation',
        {'hwid': hwid, 'profile_id': profile_id, 'success': 'true' if success else 'false', 'action_text': action_text},
    )


def get_stats(hwid: str) -> dict[str, Any]:
    return _request('get_stats', {'hwid': hwid})


def update_active_profiles(hwid: str, active_profile_ids: list[str]) -> dict[str, Any]:
    return _request('update_active_profiles', {'hwid': hwid, 'active': json.dumps(active_profile_ids)})
