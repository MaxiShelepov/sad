from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

from models import (
    DashboardResponse,
    FarmStartRequest,
    FingerprintUpdateRequest,
    LicenseCheckRequest,
    LicenseCheckResponse,
    ProfileCreate,
    ProfileImportRequest,
    ProfileRecord,
    ProfileUpdate,
    SessionPayload,
    WarmupJobRecord,
    WarmupStartRequest,
)
from repository import (
    count_profiles,
    create_profile,
    delete_profile,
    ensure_subscription,
    get_dashboard,
    get_profile,
    get_subscription,
    list_profiles,
    sanitize_hwid,
    update_fingerprint,
    update_profile,
    update_session_data,
)
from warmup_engine import create_job, launch_job, request_stop, reset_running_jobs, stop_all_for_hwid


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


@asynccontextmanager
async def lifespan(_: FastAPI):
    await reset_running_jobs(db)
    yield
    client.close()


# Create the main app without a prefix
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Warmup mobile backend online"}


@api_router.get("/health")
async def healthcheck():
    return {"success": True, "status": "ok", "service": "backend"}


@api_router.post("/license/check", response_model=LicenseCheckResponse)
async def check_license(payload: LicenseCheckRequest):
    subscription = await ensure_subscription(db, payload.hwid)
    return LicenseCheckResponse(subscription=subscription)


@api_router.get("/subscription/{hwid}", response_model=LicenseCheckResponse)
async def subscription_details(hwid: str):
    subscription = await get_subscription(db, hwid)
    return LicenseCheckResponse(subscription=subscription)


@api_router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(hwid: str = Query(..., min_length=6)):
    subscription = await get_subscription(db, hwid)
    profiles_total, profiles_running, active_jobs, latest_jobs = await get_dashboard(db, hwid)
    return DashboardResponse(
        subscription=subscription,
        profiles_total=profiles_total,
        profiles_running=profiles_running,
        active_jobs=active_jobs,
        latest_jobs=[WarmupJobRecord(**item) for item in latest_jobs],
    )


@api_router.get("/profiles", response_model=list[ProfileRecord])
async def profiles_list(hwid: str = Query(..., min_length=6)):
    await ensure_subscription(db, hwid)
    return await list_profiles(db, hwid)


@api_router.post("/profiles", response_model=ProfileRecord)
async def profiles_create(payload: ProfileCreate):
    subscription = await get_subscription(db, payload.hwid)
    if not subscription.active:
        raise HTTPException(status_code=403, detail="Подписка неактивна")
    if await count_profiles(db, payload.hwid) >= subscription.max_profiles:
        raise HTTPException(status_code=400, detail="Достигнут лимит профилей")
    return await create_profile(db, payload)


@api_router.post("/profiles/import", response_model=list[ProfileRecord])
async def import_profiles(payload: ProfileImportRequest):
    subscription = await get_subscription(db, payload.hwid)
    if not subscription.active:
        raise HTTPException(status_code=403, detail="Подписка неактивна")

    remaining = subscription.max_profiles - await count_profiles(db, payload.hwid)
    if remaining <= 0:
        raise HTTPException(status_code=400, detail="Лимит профилей исчерпан")

    created: list[ProfileRecord] = []
    for raw_line in payload.raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        delimiter = "|" if "|" in line else ";" if ";" in line else ","
        parts = [part.strip() for part in line.split(delimiter)]
        if len(parts) < 2:
            continue
        email = parts[0]
        access_token = parts[1]
        proxy = parts[2] if len(parts) > 2 else ""
        profile = await create_profile(
            db,
            ProfileCreate(
                hwid=sanitize_hwid(payload.hwid),
                name=email.split("@")[0],
                email=email,
                access_token=access_token,
                proxy=proxy,
                notes="Импортировано из batch",
                use_browser=True,
            ),
        )
        created.append(profile)
        if len(created) >= remaining:
            break
    return created


@api_router.put("/profiles/{profile_id}", response_model=ProfileRecord)
async def profiles_update(profile_id: str, payload: ProfileUpdate):
    updated = await update_profile(db, profile_id, payload.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return updated


@api_router.delete("/profiles/{profile_id}")
async def profiles_delete(profile_id: str, hwid: str = Query(..., min_length=6)):
    deleted = await delete_profile(db, profile_id, hwid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return {"success": True}


@api_router.get("/profiles/{profile_id}", response_model=ProfileRecord)
async def profile_details(profile_id: str):
    profile = await get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return profile


@api_router.get("/profiles/{profile_id}/fingerprint")
async def profile_fingerprint(profile_id: str):
    profile = await get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return {"success": True, "fingerprint": profile.fingerprint}


@api_router.put("/profiles/{profile_id}/fingerprint", response_model=ProfileRecord)
async def profile_fingerprint_update(profile_id: str, payload: FingerprintUpdateRequest):
    profile = await update_fingerprint(db, profile_id, payload.model_dump(exclude_none=True))
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return profile


@api_router.post("/profiles/{profile_id}/fingerprint/randomize", response_model=ProfileRecord)
async def profile_fingerprint_randomize(profile_id: str):
    profile = await update_fingerprint(db, profile_id, {})
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return profile


@api_router.get("/profiles/{profile_id}/session")
async def profile_session(profile_id: str):
    profile = await get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    stored = await db.profiles.find_one({"id": profile_id}, {"_id": 0, "session_data": 1})
    return {"success": True, "session_data": stored.get("session_data", {}) if stored else {}}


@api_router.put("/profiles/{profile_id}/session")
async def profile_session_update(profile_id: str, payload: SessionPayload):
    session_data = await update_session_data(db, profile_id, payload.data)
    if session_data is None:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return {"success": True, "session_data": session_data}


@api_router.get("/warmups", response_model=list[WarmupJobRecord])
async def list_warmups(hwid: str = Query(..., min_length=6)):
    docs = await db.warmup_jobs.find({"hwid": sanitize_hwid(hwid)}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    return [WarmupJobRecord(**doc) for doc in docs]


@api_router.post("/warmups/start", response_model=WarmupJobRecord)
async def start_warmup(payload: WarmupStartRequest):
    subscription = await get_subscription(db, payload.hwid)
    if not subscription.active:
        raise HTTPException(status_code=403, detail="Подписка неактивна")

    profile = await get_profile(db, payload.profile_id)
    if not profile or profile.hwid != sanitize_hwid(payload.hwid):
        raise HTTPException(status_code=404, detail="Профиль не найден")

    job_doc = await create_job(db, profile.model_dump(), sanitize_hwid(payload.hwid), payload.mode, payload.minutes)
    await launch_job(db, job_doc["id"])
    stored = await db.warmup_jobs.find_one({"id": job_doc["id"]}, {"_id": 0})
    return WarmupJobRecord(**stored)


@api_router.post("/warmups/{job_id}/stop")
async def stop_warmup(job_id: str):
    exists = await db.warmup_jobs.find_one({"id": job_id}, {"_id": 0, "id": 1})
    if not exists:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    await request_stop(db, job_id)
    return {"success": True}


@api_router.post("/farm/start", response_model=list[WarmupJobRecord])
async def start_farm(payload: FarmStartRequest):
    subscription = await get_subscription(db, payload.hwid)
    if not subscription.active or not subscription.farm_mode:
        raise HTTPException(status_code=403, detail="Ферма недоступна")

    group_id = str(uuid.uuid4())
    jobs: list[WarmupJobRecord] = []
    for item in payload.items:
        profile = await get_profile(db, item.profile_id)
        if not profile or profile.hwid != sanitize_hwid(payload.hwid):
            continue
        job_doc = await create_job(db, profile.model_dump(), sanitize_hwid(payload.hwid), item.mode, item.minutes, group_id=group_id)
        await launch_job(db, job_doc["id"])
        stored = await db.warmup_jobs.find_one({"id": job_doc["id"]}, {"_id": 0})
        jobs.append(WarmupJobRecord(**stored))

    if not jobs:
        raise HTTPException(status_code=404, detail="Не удалось запустить ферму")
    return jobs


@api_router.post("/farm/stop")
async def stop_farm(hwid: str = Query(..., min_length=6)):
    stopped_count = await stop_all_for_hwid(db, sanitize_hwid(hwid))
    return {"success": True, "stopped_count": stopped_count}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

