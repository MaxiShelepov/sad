from __future__ import annotations

import re
import uuid
import math
from datetime import datetime, timedelta, timezone

from pymongo import ReturnDocument

from fingerprints import build_fingerprint, merge_fingerprint
from models import ProfileCreate, ProfileRecord, ProfileStats, SubscriptionInfo


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_hwid(raw_hwid: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]", "", raw_hwid.strip())[:120]


def subscription_to_model(doc: dict) -> SubscriptionInfo:
    end_date = datetime.fromisoformat(doc["end_date"])
    seconds_left = (end_date - datetime.now(timezone.utc)).total_seconds()
    is_active = bool(doc.get("active")) and seconds_left > 0
    days_left = max(0, math.ceil(seconds_left / 86400)) if is_active else 0
    status_text = "Активна" if is_active else "Неактивна"
    message = (
        "Триал активирован автоматически" if doc.get("trial_used") and is_active else "Подписка требует продления"
    )
    return SubscriptionInfo(
        hwid=doc["hwid"],
        active=is_active,
        plan_name=doc.get("plan_name", "Trial"),
        max_profiles=int(doc.get("max_profiles", 3)),
        farm_mode=bool(doc.get("farm_mode", True)),
        trial_used=bool(doc.get("trial_used", False)),
        days_left=days_left,
        start_date=doc["start_date"],
        end_date=doc["end_date"],
        status_text=status_text,
        message=message,
    )


async def ensure_subscription(db, hwid: str) -> SubscriptionInfo:
    sanitized = sanitize_hwid(hwid)
    existing = await db.subscriptions.find_one({"hwid": sanitized}, {"_id": 0})
    if existing:
        return subscription_to_model(existing)

    history = await db.hwid_history.find_one({"hwid": sanitized}, {"_id": 0})
    now = datetime.now(timezone.utc)
    is_new_hwid = history is None
    end_date = now + timedelta(days=1) if is_new_hwid else now
    subscription_doc = {
        "hwid": sanitized,
        "active": is_new_hwid,
        "plan_name": "Trial 1 Day" if is_new_hwid else "Trial used",
        "max_profiles": 3,
        "farm_mode": True,
        "trial_used": is_new_hwid,
        "start_date": now.isoformat(),
        "end_date": end_date.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.subscriptions.insert_one(subscription_doc.copy())
    if is_new_hwid:
        await db.hwid_history.insert_one(
            {
                "hwid": sanitized,
                "first_seen_at": now.isoformat(),
                "trial_received": True,
            }
        )
    return subscription_to_model(subscription_doc)


async def get_subscription(db, hwid: str) -> SubscriptionInfo:
    subscription = await ensure_subscription(db, hwid)
    await db.subscriptions.update_one(
        {"hwid": subscription.hwid},
        {"$set": {"active": subscription.active, "updated_at": utc_now_iso()}},
    )
    return subscription


async def count_profiles(db, hwid: str) -> int:
    return await db.profiles.count_documents({"hwid": sanitize_hwid(hwid)})


async def list_profiles(db, hwid: str) -> list[ProfileRecord]:
    cursor = db.profiles.find({"hwid": sanitize_hwid(hwid)}, {"_id": 0}).sort("created_at", 1)
    docs = await cursor.to_list(500)
    return [ProfileRecord(**doc) for doc in docs]


async def get_profile(db, profile_id: str) -> ProfileRecord | None:
    doc = await db.profiles.find_one({"id": profile_id}, {"_id": 0})
    return ProfileRecord(**doc) if doc else None


async def create_profile(db, payload: ProfileCreate) -> ProfileRecord:
    profile_id = str(uuid.uuid4())
    now_iso = utc_now_iso()
    fingerprint = build_fingerprint(profile_id)
    profile_doc = {
        "id": profile_id,
        "hwid": sanitize_hwid(payload.hwid),
        "name": payload.name,
        "email": payload.email,
        "access_token": payload.access_token,
        "proxy": payload.proxy,
        "notes": payload.notes,
        "use_browser": payload.use_browser,
        "created_at": now_iso,
        "updated_at": now_iso,
        "is_running": False,
        "last_job_id": None,
        "session_data": {},
        "stats": ProfileStats().model_dump(),
        "fingerprint": fingerprint.model_dump(),
    }
    await db.profiles.insert_one(profile_doc.copy())
    return ProfileRecord(**profile_doc)


async def update_profile(db, profile_id: str, updates: dict) -> ProfileRecord | None:
    safe_updates = {key: value for key, value in updates.items() if value is not None}
    if not safe_updates:
        return await get_profile(db, profile_id)

    safe_updates["updated_at"] = utc_now_iso()
    updated = await db.profiles.find_one_and_update(
        {"id": profile_id},
        {"$set": safe_updates},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return ProfileRecord(**updated) if updated else None


async def delete_profile(db, profile_id: str, hwid: str) -> bool:
    result = await db.profiles.delete_one({"id": profile_id, "hwid": sanitize_hwid(hwid)})
    await db.warmup_jobs.delete_many({"profile_id": profile_id, "hwid": sanitize_hwid(hwid)})
    return result.deleted_count > 0


async def update_fingerprint(db, profile_id: str, updates: dict | None = None) -> ProfileRecord | None:
    profile = await db.profiles.find_one({"id": profile_id}, {"_id": 0, "fingerprint": 1})
    if not profile:
        return None
    fingerprint = merge_fingerprint(profile_id, profile.get("fingerprint"), updates)
    updated = await db.profiles.find_one_and_update(
        {"id": profile_id},
        {"$set": {"fingerprint": fingerprint.model_dump(), "updated_at": utc_now_iso()}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )
    return ProfileRecord(**updated) if updated else None


async def get_dashboard(db, hwid: str):
    sanitized = sanitize_hwid(hwid)
    profiles_total = await db.profiles.count_documents({"hwid": sanitized})
    profiles_running = await db.profiles.count_documents({"hwid": sanitized, "is_running": True})
    active_jobs = await db.warmup_jobs.count_documents({"hwid": sanitized, "status": {"$in": ["pending", "running"]}})
    latest_jobs = await db.warmup_jobs.find({"hwid": sanitized}, {"_id": 0}).sort("updated_at", -1).to_list(8)
    return profiles_total, profiles_running, active_jobs, latest_jobs


async def update_session_data(db, profile_id: str, payload: dict) -> dict | None:
    updated = await db.profiles.find_one_and_update(
        {"id": profile_id},
        {"$set": {"session_data": payload, "updated_at": utc_now_iso()}},
        projection={"_id": 0, "session_data": 1},
        return_document=ReturnDocument.AFTER,
    )
    return updated.get("session_data") if updated else None
