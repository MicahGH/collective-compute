import asyncio

import httpx
from fastapi import FastAPI, status
from pydantic import HttpUrl, TypeAdapter

from collective_compute.config import GatewaySettings
from collective_compute.gateway.app import create_app
from collective_compute.gateway.schemas import ProviderRegistration

PROVIDER_KEY = "provider-test-secret"
CLIENT_KEY = "client-test-secret"


def test_provider_registration_requires_provider_api_key() -> None:
    """Provider-only endpoint rejects anonymous and client-authenticated callers."""
    app = create_app(settings=GatewaySettings(PROVIDER_KEY, CLIENT_KEY))
    anonymous, client_key, provider_key = asyncio.run(
        _post_registration_requests(app, _registration().model_dump(mode="json"))
    )

    assert anonymous.status_code == status.HTTP_401_UNAUTHORIZED
    assert client_key.status_code == status.HTTP_401_UNAUTHORIZED
    assert provider_key.status_code == status.HTTP_201_CREATED


def test_provider_list_requires_client_api_key() -> None:
    """Client-visible provider state is not exposed without client authentication."""
    app = create_app(settings=GatewaySettings(PROVIDER_KEY, CLIENT_KEY))
    anonymous, provider_key, client_key = asyncio.run(_get_provider_requests(app))

    assert anonymous.status_code == status.HTTP_401_UNAUTHORIZED
    assert provider_key.status_code == status.HTTP_401_UNAUTHORIZED
    assert client_key.status_code == status.HTTP_200_OK


async def _post_registration_requests(
    app: FastAPI, payload: dict[str, object]
) -> tuple[httpx.Response, httpx.Response, httpx.Response]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        anonymous = await client.post("/providers/register", json=payload)
        client_key = await client.post(
            "/providers/register", json=payload, headers={"X-API-Key": CLIENT_KEY}
        )
        provider_key = await client.post(
            "/providers/register", json=payload, headers={"X-API-Key": PROVIDER_KEY}
        )
    return anonymous, client_key, provider_key


async def _get_provider_requests(
    app: FastAPI,
) -> tuple[httpx.Response, httpx.Response, httpx.Response]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        anonymous = await client.get("/providers")
        provider_key = await client.get("/providers", headers={"X-API-Key": PROVIDER_KEY})
        client_key = await client.get("/providers", headers={"X-API-Key": CLIENT_KEY})
    return anonymous, provider_key, client_key


def _registration() -> ProviderRegistration:
    return ProviderRegistration(
        node_id="node-a",
        endpoint_url=TypeAdapter(HttpUrl).validate_python("http://node-a.example.com"),
        gpu_name="RTX 4090",
        vram_gb=24,
        max_gpu_usage_percent=50,
    )
