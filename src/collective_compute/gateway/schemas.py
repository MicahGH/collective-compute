from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class ProviderStatus(StrEnum):
    """The gateway's current assessment of a provider node."""

    ONLINE = "online"
    OFFLINE = "offline"


class ProviderRegistration(BaseModel):
    """Provider data supplied when a node joins the gateway."""

    node_id: str = Field(min_length=1, max_length=128)
    endpoint_url: HttpUrl
    gpu_name: str = Field(min_length=1, max_length=256)
    vram_gb: float = Field(gt=0)
    max_gpu_usage_percent: int = Field(ge=1, le=100)
    availability: str = Field(default="always", max_length=256)


class ProviderRecord(ProviderRegistration):
    """A registered provider with gateway-managed liveness fields."""

    status: ProviderStatus
    last_heartbeat_at: datetime


class HeartbeatRequest(BaseModel):
    """Liveness update sent by a registered provider node."""

    node_id: str = Field(min_length=1, max_length=128)


class GenerationParameters(BaseModel):
    """Supported controls for text generation."""

    max_tokens: int = Field(default=256, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0, le=2)


class InferenceRequest(BaseModel):
    """Client request to run a model against a prompt."""

    model: str = Field(min_length=1, max_length=256)
    prompt: str = Field(min_length=1)
    parameters: GenerationParameters = Field(default_factory=GenerationParameters)


class InferenceResponse(BaseModel):
    """Gateway response containing generated text and routing metadata."""

    job_id: str
    provider_id: str
    model: str
    response: str
