from __future__ import annotations

import asyncio
import random
import time
import uuid

from pymongo import ReturnDocument

from repository import utc_now_iso


ACTION_POOLS = {
    "calm": [
        "Открыт Яндекс Музыка",
        "Просмотрен Дзен",
        "Проверена почта",
        "Сохранено состояние сессии",
        "Выполнен мягкий поиск по сервисам",
    ],
    "balanced": [
        "Открыт Маркет и просмотрены товары",
        "Проверены Карты и маршрут",
        "Выполнен поиск с исправлением опечатки",
        "Просмотрен Кинопоиск",
        "Синхронизированы активные профили",
        "Обновлены метрики доверия",
    ],
    "turbo": [
        "Пакетный обход сервисов Яндекса завершён",
        "Проверены Музыка, Карты и Маркет",
        "Выполнена серия запросов к профилю",
        "Сохранён прогресс активной фермы",
        "Обновлён след активности пользователя",
        "Выполнена ускоренная операция прогрева",
    ],
}


_active_tasks: dict[str, asyncio.Task] = {}


def _build_log(level: str, message: str) -> dict:
    return {"timestamp": utc_now_iso(), "level": level, "message": message}


async def reset_running_jobs(db) -> None:
    now = utc_now_iso()
    await db.warmup_jobs.update_many(
        {"status": {"$in": ["pending", "running"]}},
        {
            "$set": {
                "status": "stopped",
                "current_action": "Сервер перезапущен",
                "updated_at": now,
            },
            "$push": {"logs": {"$each": [_build_log("warning", "Задача остановлена после перезапуска сервера")], "$slice": -120}},
        },
    )
    await db.profiles.update_many({"is_running": True}, {"$set": {"is_running": False, "updated_at": now}})


async def create_job(db, profile: dict, hwid: str, mode: str, minutes: int, group_id: str | None = None) -> dict:
    job_id = str(uuid.uuid4())
    now = utc_now_iso()
    job_doc = {
        "id": job_id,
        "hwid": hwid,
        "profile_id": profile["id"],
        "profile_name": profile["name"],
        "email": profile["email"],
        "group_id": group_id,
        "mode": mode,
        "minutes": minutes,
        "status": "pending",
        "current_action": "Подготовка к запуску",
        "created_at": now,
        "started_at": None,
        "updated_at": now,
        "stop_requested": False,
        "logs": [_build_log("system", "Задача создана и ожидает запуска")],
        "metrics": {
            "trust_score": int(profile.get("stats", {}).get("trust_score", 72)),
            "total_operations": int(profile.get("stats", {}).get("total_operations", 0)),
            "successful_operations": int(profile.get("stats", {}).get("successful_operations", 0)),
            "opm": 0.0,
            "elapsed_seconds": 0,
            "progress": 0.0,
        },
    }
    await db.warmup_jobs.insert_one(job_doc.copy())
    return job_doc


async def launch_job(db, job_id: str) -> None:
    task = asyncio.create_task(_run_job(db, job_id))
    _active_tasks[job_id] = task


async def request_stop(db, job_id: str) -> None:
    await db.warmup_jobs.update_one(
        {"id": job_id},
        {
            "$set": {"stop_requested": True, "updated_at": utc_now_iso()},
            "$push": {"logs": {"$each": [_build_log("warning", "Получен запрос на остановку")], "$slice": -120}},
        },
    )


async def stop_all_for_hwid(db, hwid: str) -> int:
    jobs = await db.warmup_jobs.find({"hwid": hwid, "status": {"$in": ["pending", "running"]}}, {"_id": 0, "id": 1}).to_list(100)
    for job in jobs:
        await request_stop(db, job["id"])
    return len(jobs)


async def _update_profile_stats(db, profile_id: str, action: str, success: bool) -> dict:
    updated = await db.profiles.find_one_and_update(
        {"id": profile_id},
        {
            "$inc": {
                "stats.total_operations": 1,
                "stats.successful_operations": 1 if success else 0,
            },
            "$set": {
                "stats.last_action": action,
                "updated_at": utc_now_iso(),
            },
        },
        projection={"_id": 0, "stats": 1},
        return_document=ReturnDocument.AFTER,
    )
    stats = updated.get("stats", {}) if updated else {}
    total = max(1, int(stats.get("total_operations", 0)))
    successful = int(stats.get("successful_operations", 0))
    success_rate = successful / total
    trust_score = max(35, min(99, int(48 + success_rate * 51)))
    await db.profiles.update_one({"id": profile_id}, {"$set": {"stats.trust_score": trust_score}})
    stats["trust_score"] = trust_score
    return stats


async def _finish_job(db, job: dict, status: str, action_text: str, level: str = "system") -> None:
    now = utc_now_iso()
    await db.warmup_jobs.update_one(
        {"id": job["id"]},
        {
            "$set": {"status": status, "current_action": action_text, "updated_at": now},
            "$push": {"logs": {"$each": [_build_log(level, action_text)], "$slice": -120}},
        },
    )
    await db.profiles.update_one(
        {"id": job["profile_id"]},
        {"$set": {"is_running": False, "updated_at": now}},
    )


async def _run_job(db, job_id: str) -> None:
    started_at = utc_now_iso()
    monotonic_start = time.monotonic()
    try:
        job = await db.warmup_jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            return

        await db.warmup_jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": "running",
                    "started_at": started_at,
                    "updated_at": started_at,
                    "current_action": "Прогрев запущен",
                },
                "$push": {"logs": {"$each": [_build_log("system", "Прогрев успешно запущен")], "$slice": -120}},
            },
        )
        await db.profiles.update_one(
            {"id": job["profile_id"]},
            {"$set": {"is_running": True, "last_job_id": job_id, "updated_at": started_at}},
        )

        action_pool = ACTION_POOLS.get(job["mode"], ACTION_POOLS["balanced"])
        target_seconds = int(job["minutes"]) * 60

        while True:
            await asyncio.sleep(random.uniform(2.5, 5.5))
            current_job = await db.warmup_jobs.find_one({"id": job_id}, {"_id": 0})
            if not current_job:
                return

            elapsed_seconds = int(time.monotonic() - monotonic_start)
            if current_job.get("stop_requested"):
                await _finish_job(db, current_job, "stopped", "Прогрев остановлен пользователем", "warning")
                return
            if elapsed_seconds >= target_seconds:
                await _finish_job(db, current_job, "completed", "Прогрев завершён", "success")
                return

            action_text = random.choice(action_pool)
            success = random.random() > 0.14
            stats = await _update_profile_stats(db, current_job["profile_id"], action_text, success)
            elapsed_minutes = max(elapsed_seconds / 60, 1 / 60)
            metrics = {
                "trust_score": int(stats.get("trust_score", 72)),
                "total_operations": int(stats.get("total_operations", 0)),
                "successful_operations": int(stats.get("successful_operations", 0)),
                "opm": round(int(stats.get("total_operations", 0)) / elapsed_minutes, 2),
                "elapsed_seconds": elapsed_seconds,
                "progress": round(min(elapsed_seconds / target_seconds, 1), 3),
            }

            level = "success" if success else "warning"
            message = f"{action_text} — {'успешно' if success else 'с предупреждением'}"
            await db.warmup_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "current_action": action_text,
                        "updated_at": utc_now_iso(),
                        "metrics": metrics,
                    },
                    "$push": {"logs": {"$each": [_build_log(level, message)], "$slice": -120}},
                },
            )
    except Exception as exc:  # noqa: BLE001
        failed_job = await db.warmup_jobs.find_one({"id": job_id}, {"_id": 0})
        if failed_job:
            await _finish_job(db, failed_job, "error", f"Ошибка прогрева: {exc}", "error")
    finally:
        _active_tasks.pop(job_id, None)
