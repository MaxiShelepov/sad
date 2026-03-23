from __future__ import annotations

import asyncio
import json
import math
import re
from datetime import datetime, timezone

from fingerprints import build_fingerprint, merge_fingerprint
from models import ProfileCreate, ProfileRecord, ProfileStats, SubscriptionInfo
from remote_vortex import (
    VortexRemoteError,
    check_hwid,
    create_profile as remote_create_profile,
    delete_profile as remote_delete_profile,
    get_profiles as remote_get_profiles,
    load_fingerprint as remote_load_fingerprint,
    load_session as remote_load_session,
    save_fingerprint as remote_save_fingerprint,
    save_session as remote_save_session,
    update_profile as remote_update_profile,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_hwid(raw_hwid: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]", "", raw_hwid.strip())[:120]


def _parse_datetime(value: str) -> datetime:
    if 'T' in value:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    if ' ' in value:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    return datetime.strptime(value, '%Y-%m-%d').replace(tzinfo=timezone.utc)


def subscription_to_model(doc: dict) -> SubscriptionInfo:
    end_date = _parse_datetime(doc['end_date'])
    seconds_left = (end_date - datetime.now(timezone.utc)).total_seconds()
    is_active = bool(doc.get('active')) and seconds_left > 0
    days_left = max(0, math.ceil(seconds_left / 86400)) if is_active else 0
    return SubscriptionInfo(
        hwid=doc['hwid'],
        active=is_active,
        plan_name=doc.get('plan_name', 'Trial'),
        max_profiles=int(doc.get('max_profiles', 0) or 0),
        farm_mode=bool(doc.get('farm_mode', False)),
        trial_used=bool(doc.get('trial_used', False)),
        days_left=days_left,
        start_date=doc.get('start_date', ''),
        end_date=doc.get('end_date', ''),
        status_text='Активна' if is_active else 'Неактивна',
        message=doc.get('comment') or ('Триал активирован автоматически' if is_active else 'Подписка требует продления'),
    )


async def ensure_subscription(db, hwid: str) -> SubscriptionInfo:
    response = await asyncio.to_thread(check_hwid, sanitize_hwid(hwid))
    return subscription_to_model(response.get('subscription', {}))


async def get_subscription(db, hwid: str) -> SubscriptionInfo:
    return await ensure_subscription(db, hwid)


async def count_profiles(db, hwid: str) -> int:
    response = await asyncio.to_thread(remote_get_profiles, sanitize_hwid(hwid))
    return len(response.get('profiles', []))


async def _running_profile_index(db, hwid: str) -> tuple[set[str], dict[str, str | None], dict[str, dict]]:
    docs = await db.warmup_jobs.find(
        {'hwid': hwid},
        {'_id': 0, 'id': 1, 'profile_id': 1, 'status': 1, 'updated_at': 1, 'metrics': 1},
    ).sort('updated_at', -1).to_list(300)
    running = {doc['profile_id'] for doc in docs if doc.get('status') in {'pending', 'running'}}
    latest = {}
    latest_metrics = {}
    for doc in docs:
        latest.setdefault(doc['profile_id'], doc['id'])
        latest_metrics.setdefault(doc['profile_id'], doc.get('metrics', {}))
    return running, latest, latest_metrics


async def _load_profile_fingerprint(hwid: str, profile_id: str) -> dict:
    try:
        response = await asyncio.to_thread(remote_load_fingerprint, hwid, profile_id)
        raw = response.get('fingerprint', {}) or {}
    except VortexRemoteError:
        raw = {}
    return merge_fingerprint(profile_id, build_fingerprint(profile_id).model_dump(), raw).model_dump()


def _profile_to_record(remote_profile: dict, fingerprint: dict, is_running: bool, last_job_id: str | None, runtime_metrics: dict | None = None) -> ProfileRecord:
    created_at = remote_profile.get('created_at', utc_now_iso())
    runtime_metrics = runtime_metrics or {}
    trust_score = int(runtime_metrics.get('trust_score', remote_profile.get('trust_score', 0)) or 0)
    total_operations = int(runtime_metrics.get('total_operations', remote_profile.get('total_operations', 0)) or 0)
    successful_operations = int(runtime_metrics.get('successful_operations', remote_profile.get('successful_operations', 0)) or 0)
    return ProfileRecord(
        id=remote_profile['id'],
        hwid=remote_profile.get('hwid', ''),
        name=remote_profile.get('name') or remote_profile.get('email', '').split('@')[0],
        email=remote_profile.get('email', ''),
        access_token=remote_profile.get('access_token', ''),
        proxy=remote_profile.get('proxy', ''),
        notes=remote_profile.get('comment', ''),
        use_browser=bool(int(remote_profile.get('use_browser', 1) or 0)),
        created_at=created_at,
        updated_at=remote_profile.get('updated_at', created_at),
        is_running=is_running,
        last_job_id=last_job_id,
        stats=ProfileStats(
            trust_score=trust_score,
            total_operations=total_operations,
            successful_operations=successful_operations,
            last_action=remote_profile.get('last_action', 'Ожидание запуска'),
        ),
        fingerprint=merge_fingerprint(remote_profile['id'], build_fingerprint(remote_profile['id']).model_dump(), fingerprint).model_dump(),
    )


async def list_profiles(db, hwid: str) -> list[ProfileRecord]:
    sanitized = sanitize_hwid(hwid)
    response = await asyncio.to_thread(remote_get_profiles, sanitized)
    profiles = response.get('profiles', [])
    running_ids, latest_job_ids, metrics_by_profile = await _running_profile_index(db, sanitized)
    fingerprints = await asyncio.gather(*[_load_profile_fingerprint(sanitized, item['id']) for item in profiles])
    return [
        _profile_to_record(
            profile,
            fingerprint,
            profile['id'] in running_ids,
            latest_job_ids.get(profile['id']),
            metrics_by_profile.get(profile['id']),
        )
        for profile, fingerprint in zip(profiles, fingerprints)
    ]


async def get_profile(db, hwid: str, profile_id: str) -> ProfileRecord | None:
    profiles = await list_profiles(db, hwid)
    return next((item for item in profiles if item.id == profile_id), None)


async def create_profile(db, payload: ProfileCreate) -> ProfileRecord:
    sanitized = sanitize_hwid(payload.hwid)
    response = await asyncio.to_thread(
        remote_create_profile,
        sanitized,
        payload.email,
        payload.access_token,
        payload.proxy,
        payload.name,
        payload.use_browser,
    )
    remote_profile = response.get('profile', {})
    fingerprint = build_fingerprint(remote_profile['id']).model_dump()
    await asyncio.to_thread(remote_save_fingerprint, sanitized, remote_profile['id'], fingerprint)
    return _profile_to_record({**remote_profile, 'hwid': sanitized, 'use_browser': int(payload.use_browser)}, fingerprint, False, None)


async def update_profile(db, profile_id: str, hwid: str, updates: dict) -> ProfileRecord | None:
    safe_updates = {key: value for key, value in updates.items() if value is not None}
    if not safe_updates:
        return await get_profile(db, hwid, profile_id)
    await asyncio.to_thread(remote_update_profile, sanitize_hwid(hwid), profile_id, safe_updates)
    return await get_profile(db, hwid, profile_id)


async def delete_profile(db, profile_id: str, hwid: str) -> bool:
    await asyncio.to_thread(remote_delete_profile, sanitize_hwid(hwid), profile_id)
    await db.warmup_jobs.delete_many({'profile_id': profile_id, 'hwid': sanitize_hwid(hwid)})
    return True


async def update_fingerprint(db, hwid: str, profile_id: str, updates: dict | None = None) -> ProfileRecord | None:
    current = await _load_profile_fingerprint(sanitize_hwid(hwid), profile_id)
    fingerprint = merge_fingerprint(profile_id, current, updates).model_dump()
    await asyncio.to_thread(remote_save_fingerprint, sanitize_hwid(hwid), profile_id, fingerprint)
    return await get_profile(db, hwid, profile_id)


async def get_dashboard(db, hwid: str):
    sanitized = sanitize_hwid(hwid)
    profiles_total = await count_profiles(db, sanitized)
    profiles_running = await db.warmup_jobs.count_documents({'hwid': sanitized, 'status': {'$in': ['pending', 'running']}})
    active_jobs = profiles_running
    latest_jobs = await db.warmup_jobs.find({'hwid': sanitized}, {'_id': 0}).sort('updated_at', -1).to_list(8)
    return profiles_total, profiles_running, active_jobs, latest_jobs


async def load_session_data(hwid: str, profile_id: str) -> dict:
    response = await asyncio.to_thread(remote_load_session, sanitize_hwid(hwid), profile_id)
    raw = response.get('session_data', '{}')
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or '{}')
    except json.JSONDecodeError:
        return {}


async def update_session_data(hwid: str, profile_id: str, payload: dict) -> dict | None:
    await asyncio.to_thread(remote_save_session, sanitize_hwid(hwid), profile_id, payload)
    return payload
