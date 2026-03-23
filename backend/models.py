from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


WarmupMode = Literal["calm", "balanced", "turbo"]
WarmupStatus = Literal["idle", "pending", "running", "stopped", "completed", "error"]


class LicenseCheckRequest(BaseModel):
    hwid: str = Field(min_length=6, max_length=120)


class SubscriptionInfo(BaseModel):
    hwid: str
    active: bool
    plan_name: str
    max_profiles: int
    farm_mode: bool
    trial_used: bool
    days_left: int
    start_date: str
    end_date: str
    status_text: str
    message: str


class LicenseCheckResponse(BaseModel):
    success: bool = True
    subscription: SubscriptionInfo


class ProfileStats(BaseModel):
    trust_score: int = 72
    total_operations: int = 0
    successful_operations: int = 0
    last_action: str = "Ожидание запуска"


class FingerprintData(BaseModel):
    profile_id: str
    browser: str = "Chrome"
    browser_version: str = "131"
    user_agent: str = ""
    platform: str = "Linux armv8l"
    os_name: str = "Android"
    os_category: str = "android_14"
    screen_width: int = 1080
    screen_height: int = 2400
    timezone: str = "Europe/Moscow"
    webgl_vendor_group: str = "Qualcomm Adreno"
    webgl_renderer: str = "Adreno 740"
    connection_type: str = "4g"
    hardware_concurrency: int = 8
    device_memory: int = 8
    color_depth: int = 24
    languages: list[str] = Field(default_factory=lambda: ["ru-RU", "ru", "en-US"])
    is_mobile: bool = True
    touch_points: int = 5


class ProfileBase(BaseModel):
    hwid: str = Field(min_length=6, max_length=120)
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=4, max_length=120)
    access_token: str = Field(default="", max_length=2048)
    proxy: str = Field(default="", max_length=255)
    notes: str = Field(default="", max_length=500)
    use_browser: bool = True


class ProfileCreate(ProfileBase):
    pass


class ProfileImportRequest(BaseModel):
    hwid: str = Field(min_length=6, max_length=120)
    raw_text: str = Field(min_length=3)


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    email: str | None = Field(default=None, min_length=4, max_length=120)
    access_token: str | None = Field(default=None, max_length=2048)
    proxy: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=500)
    use_browser: bool | None = None


class ProfileRecord(ProfileBase):
    id: str
    created_at: str
    updated_at: str
    is_running: bool = False
    last_job_id: str | None = None
    stats: ProfileStats = Field(default_factory=ProfileStats)
    fingerprint: FingerprintData


class FingerprintUpdateRequest(BaseModel):
    browser: str | None = None
    browser_version: str | None = None
    user_agent: str | None = None
    platform: str | None = None
    os_name: str | None = None
    os_category: str | None = None
    screen_width: int | None = None
    screen_height: int | None = None
    timezone: str | None = None
    webgl_vendor_group: str | None = None
    webgl_renderer: str | None = None
    connection_type: str | None = None
    hardware_concurrency: int | None = None
    device_memory: int | None = None
    color_depth: int | None = None


class SessionPayload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class WarmupLogEntry(BaseModel):
    timestamp: str
    level: Literal["system", "success", "warning", "error", "operation", "info"]
    message: str


class WarmupMetrics(BaseModel):
    trust_score: int = 72
    total_operations: int = 0
    successful_operations: int = 0
    opm: float = 0.0
    elapsed_seconds: int = 0
    progress: float = 0.0


class WarmupStartRequest(BaseModel):
    hwid: str = Field(min_length=6, max_length=120)
    profile_id: str
    mode: WarmupMode = "balanced"
    minutes: int = Field(default=15, ge=1, le=240)


class FarmWarmupItem(BaseModel):
    profile_id: str
    mode: WarmupMode = "balanced"
    minutes: int = Field(default=15, ge=1, le=240)


class FarmStartRequest(BaseModel):
    hwid: str = Field(min_length=6, max_length=120)
    items: list[FarmWarmupItem] = Field(min_length=1, max_length=12)


class WarmupJobRecord(BaseModel):
    id: str
    hwid: str
    profile_id: str
    profile_name: str
    email: str
    group_id: str | None = None
    mode: WarmupMode
    minutes: int
    status: WarmupStatus
    current_action: str
    created_at: str
    started_at: str | None = None
    updated_at: str
    logs: list[WarmupLogEntry] = Field(default_factory=list)
    metrics: WarmupMetrics = Field(default_factory=WarmupMetrics)


class DashboardResponse(BaseModel):
    subscription: SubscriptionInfo
    profiles_total: int
    profiles_running: int
    active_jobs: int
    latest_jobs: list[WarmupJobRecord]
