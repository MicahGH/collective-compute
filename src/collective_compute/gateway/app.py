from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from hmac import compare_digest
from typing import Annotated, cast
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, status

from collective_compute.config import GatewaySettings

from .registry import ProviderRegistry
from .schemas import (
    HeartbeatRequest,
    InferenceRequest,
    InferenceResponse,
    ProviderRecord,
    ProviderRegistration,
)

ApiKeyHeader = Annotated[str | None, Header(alias="X-API-Key")]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Create and close shared outbound HTTP resources."""
    if app.state.settings is None:
        app.state.settings = GatewaySettings.from_environment()
    app.state.http_client = httpx.AsyncClient(timeout=60.0)
    yield
    await app.state.http_client.aclose()


def create_app(
    registry: ProviderRegistry | None = None, settings: GatewaySettings | None = None
) -> FastAPI:
    """Build the gateway application with an optional provider registry."""
    app = FastAPI(title="CollectiveCompute Gateway", version="0.1.0", lifespan=lifespan)
    app.state.registry = registry or ProviderRegistry()
    app.state.settings = settings

    @app.post("/providers/register", status_code=status.HTTP_201_CREATED)
    async def register_provider(  # pyright: ignore[reportUnusedFunction]
        payload: ProviderRegistration,
        request: Request,
        api_key: ApiKeyHeader = None,
    ) -> ProviderRecord:
        _require_api_key(api_key, _settings(request).provider_api_key)
        return request.app.state.registry.register(payload)

    @app.post("/providers/heartbeat")
    async def provider_heartbeat(  # pyright: ignore[reportUnusedFunction]
        payload: HeartbeatRequest,
        request: Request,
        api_key: ApiKeyHeader = None,
    ) -> ProviderRecord:
        _require_api_key(api_key, _settings(request).provider_api_key)
        provider = request.app.state.registry.heartbeat(payload.node_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="Provider is not registered")
        return provider

    @app.get("/providers")
    async def list_providers(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        api_key: ApiKeyHeader = None,
    ) -> list[ProviderRecord]:
        _require_api_key(api_key, _settings(request).client_api_key)
        return request.app.state.registry.all_providers()

    @app.post("/inference")
    async def inference(  # pyright: ignore[reportUnusedFunction]
        payload: InferenceRequest,
        request: Request,
        api_key: ApiKeyHeader = None,
    ) -> InferenceResponse:
        settings = _settings(request)
        _require_api_key(api_key, settings.client_api_key)
        provider = request.app.state.registry.available_provider()
        if provider is None:
            raise HTTPException(status_code=503, detail="No providers are currently online")

        try:
            response = await request.app.state.http_client.post(
                f"{str(provider.endpoint_url).rstrip('/')}/inference",
                json=payload.model_dump(),
                headers={"X-API-Key": settings.provider_api_key},
            )
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=502, detail="Selected provider could not complete inference"
            ) from exc

        generated_text = result.get("response")
        if not isinstance(generated_text, str):
            raise HTTPException(
                status_code=502, detail="Provider returned an invalid inference response"
            )
        return InferenceResponse(
            job_id=str(uuid4()),
            provider_id=provider.node_id,
            model=payload.model,
            response=generated_text,
        )

    return app


app = create_app()


def _settings(request: Request) -> GatewaySettings:
    """Return the typed gateway settings stored on the application."""
    return cast("GatewaySettings", request.app.state.settings)


def _require_api_key(provided_key: str | None, expected_key: str) -> None:
    """Reject missing or incorrect API keys without leaking secret values."""
    if provided_key is None or not compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
