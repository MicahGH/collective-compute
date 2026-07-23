from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, Request, status

from .registry import ProviderRegistry
from .schemas import (
    HeartbeatRequest,
    InferenceRequest,
    InferenceResponse,
    ProviderRecord,
    ProviderRegistration,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Create and close shared outbound HTTP resources."""
    app.state.http_client = httpx.AsyncClient(timeout=60.0)
    yield
    await app.state.http_client.aclose()


def create_app(registry: ProviderRegistry | None = None) -> FastAPI:
    """Build the gateway application with an optional provider registry."""
    app = FastAPI(title="CollectiveCompute Gateway", version="0.1.0", lifespan=lifespan)
    app.state.registry = registry or ProviderRegistry()

    @app.post("/providers/register", status_code=status.HTTP_201_CREATED)
    async def register_provider(  # pyright: ignore[reportUnusedFunction]
        payload: ProviderRegistration, request: Request
    ) -> ProviderRecord:
        return request.app.state.registry.register(payload)

    @app.post("/providers/heartbeat")
    async def provider_heartbeat(  # pyright: ignore[reportUnusedFunction]
        payload: HeartbeatRequest, request: Request
    ) -> ProviderRecord:
        provider = request.app.state.registry.heartbeat(payload.node_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="Provider is not registered")
        return provider

    @app.get("/providers")
    async def list_providers(  # pyright: ignore[reportUnusedFunction]
        request: Request,
    ) -> list[ProviderRecord]:
        return request.app.state.registry.all_providers()

    @app.post("/inference")
    async def inference(  # pyright: ignore[reportUnusedFunction]
        payload: InferenceRequest, request: Request
    ) -> InferenceResponse:
        provider = request.app.state.registry.available_provider()
        if provider is None:
            raise HTTPException(status_code=503, detail="No providers are currently online")

        try:
            response = await request.app.state.http_client.post(
                f"{str(provider.endpoint_url).rstrip('/')}/inference",
                json=payload.model_dump(),
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
