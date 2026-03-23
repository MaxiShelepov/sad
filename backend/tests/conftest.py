import os

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL fixture from environment variables."""
    backend_url = os.environ.get("EXPO_BACKEND_URL") or os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    if not backend_url:
        pytest.skip("EXPO_BACKEND_URL/EXPO_PUBLIC_BACKEND_URL is not configured")
    return backend_url.rstrip("/")


@pytest.fixture(scope="session")
def api_client() -> requests.Session:
    """Shared requests session for API tests."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session
