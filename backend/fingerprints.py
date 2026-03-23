from __future__ import annotations

import random

from models import FingerprintData


_BROWSER_PRESETS = {
    "Chrome": ["128", "129", "130", "131"],
    "Edge": ["127", "128", "129"],
    "Firefox": ["128", "129", "130"],
    "Safari": ["17.5", "17.6", "18.0"],
}

_OS_PRESETS = {
    "android_14": {
        "os_name": "Android",
        "platform": "Linux armv8l",
        "screens": [(1080, 2400), (1080, 2340), (1440, 3120)],
        "touch_points": 5,
    },
    "android_13": {
        "os_name": "Android",
        "platform": "Linux armv8l",
        "screens": [(1080, 2400), (1170, 2532), (1220, 2712)],
        "touch_points": 5,
    },
    "ios_17": {
        "os_name": "iOS",
        "platform": "iPhone",
        "screens": [(1179, 2556), (1290, 2796), (1170, 2532)],
        "touch_points": 5,
    },
}

_GPU_PRESETS = {
    "Qualcomm Adreno": ["Adreno 730", "Adreno 740", "Adreno 750"],
    "ARM Mali": ["Mali-G715", "Mali-G710", "Mali-G610"],
    "Apple Mobile": ["Apple GPU A17", "Apple GPU A16", "Apple GPU A15"],
}

_TIMEZONES = [
    "Europe/Moscow",
    "Europe/Berlin",
    "Asia/Yekaterinburg",
    "Asia/Almaty",
    "Europe/Istanbul",
]


def _build_user_agent(browser: str, version: str, os_name: str, os_category: str) -> str:
    if os_name == "iOS":
        return (
            f"Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
            f"AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Mobile/15E148 Safari/604.1"
        )
    if browser == "Firefox":
        return (
            f"Mozilla/5.0 (Android 14; Mobile; rv:{version}.0) "
            f"Gecko/{version}.0 Firefox/{version}.0"
        )
    if browser == "Edge":
        return (
            f"Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{version}.0.0.0 Mobile Safari/537.36 EdgA/{version}.0.0.0"
        )
    return (
        f"Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{version}.0.0.0 Mobile Safari/537.36"
    )


def build_fingerprint(profile_id: str, overrides: dict | None = None) -> FingerprintData:
    overrides = overrides or {}
    os_category = overrides.get("os_category") or random.choice(list(_OS_PRESETS.keys()))
    os_preset = _OS_PRESETS[os_category]
    browser_options = ["Safari"] if os_preset["os_name"] == "iOS" else ["Chrome", "Edge", "Firefox"]
    browser = overrides.get("browser") or random.choice(browser_options)
    browser_version = overrides.get("browser_version") or random.choice(_BROWSER_PRESETS[browser])
    screen_width, screen_height = random.choice(os_preset["screens"])
    gpu_group = overrides.get("webgl_vendor_group") or random.choice(list(_GPU_PRESETS.keys()))
    renderer = overrides.get("webgl_renderer") or random.choice(_GPU_PRESETS[gpu_group])
    os_name = overrides.get("os_name") or os_preset["os_name"]

    fingerprint = FingerprintData(
        profile_id=profile_id,
        browser=browser,
        browser_version=browser_version,
        platform=overrides.get("platform") or os_preset["platform"],
        os_name=os_name,
        os_category=os_category,
        screen_width=overrides.get("screen_width") or screen_width,
        screen_height=overrides.get("screen_height") or screen_height,
        timezone=overrides.get("timezone") or random.choice(_TIMEZONES),
        webgl_vendor_group=gpu_group,
        webgl_renderer=renderer,
        connection_type=overrides.get("connection_type") or random.choice(["4g", "wifi"]),
        hardware_concurrency=overrides.get("hardware_concurrency") or random.choice([6, 8, 12]),
        device_memory=overrides.get("device_memory") or random.choice([6, 8, 12]),
        color_depth=overrides.get("color_depth") or 24,
        touch_points=os_preset["touch_points"],
        user_agent=overrides.get("user_agent") or _build_user_agent(browser, browser_version, os_name, os_category),
    )
    return fingerprint


def merge_fingerprint(profile_id: str, current_data: dict | None, updates: dict | None) -> FingerprintData:
    merged = {**(current_data or {}), **(updates or {})}
    merged.setdefault("profile_id", profile_id)
    fingerprint = build_fingerprint(profile_id, merged)

    if merged.get("platform"):
        fingerprint.platform = merged["platform"]
    if merged.get("screen_width"):
        fingerprint.screen_width = int(merged["screen_width"])
    if merged.get("screen_height"):
        fingerprint.screen_height = int(merged["screen_height"])
    if merged.get("timezone"):
        fingerprint.timezone = merged["timezone"]
    if merged.get("webgl_vendor_group"):
        fingerprint.webgl_vendor_group = merged["webgl_vendor_group"]
    if merged.get("webgl_renderer"):
        fingerprint.webgl_renderer = merged["webgl_renderer"]
    if merged.get("user_agent"):
        fingerprint.user_agent = merged["user_agent"]
    return fingerprint
