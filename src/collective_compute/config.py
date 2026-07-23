"""Environment-backed configuration shared by CollectiveCompute services."""

from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

_ = load_dotenv()

MAX_GPU_USAGE_PERCENT = 100


class ConfigurationError(ValueError):
    """Raised when a required service setting is missing or malformed."""


def required_environment(name: str) -> str:
    """Return a non-empty environment variable or raise a clear configuration error."""
    value = getenv(name)
    if value is None or not value.strip():
        message = f"{name} must be set"
        raise ConfigurationError(message)
    return value


@dataclass(frozen=True)
class GatewaySettings:
    """Secrets required by the gateway."""

    provider_api_key: str
    client_api_key: str

    @classmethod
    def from_environment(cls) -> "GatewaySettings":
        """Load gateway secrets from the process environment."""
        return cls(
            provider_api_key=required_environment("CC_PROVIDER_API_KEY"),
            client_api_key=required_environment("CC_CLIENT_API_KEY"),
        )


@dataclass(frozen=True)
class NodeSettings:
    """Identity, capacity, and gateway connection settings for one provider node."""

    gateway_url: str
    node_id: str
    endpoint_url: str
    provider_api_key: str
    gpu_name: str
    vram_gb: float
    max_gpu_usage_percent: int
    availability: str
    heartbeat_interval_seconds: float

    @classmethod
    def from_environment(cls) -> "NodeSettings":
        """Load provider-node settings from the process environment."""
        return cls(
            gateway_url=required_environment("CC_GATEWAY_URL").rstrip("/"),
            node_id=required_environment("CC_NODE_ID"),
            endpoint_url=required_environment("CC_NODE_ENDPOINT_URL"),
            provider_api_key=required_environment("CC_PROVIDER_API_KEY"),
            gpu_name=required_environment("CC_NODE_GPU_NAME"),
            vram_gb=_positive_float("CC_NODE_VRAM_GB"),
            max_gpu_usage_percent=_percentage("CC_NODE_MAX_GPU_USAGE_PERCENT"),
            availability=getenv("CC_NODE_AVAILABILITY", "always"),
            heartbeat_interval_seconds=_positive_float(
                "CC_HEARTBEAT_INTERVAL_SECONDS", default=15.0
            ),
        )


def _positive_float(name: str, default: float | None = None) -> float:
    value = getenv(name)
    if value is None and default is not None:
        return default
    try:
        parsed = float(required_environment(name))
    except ValueError as exc:
        message = f"{name} must be a number"
        raise ConfigurationError(message) from exc
    if parsed <= 0:
        message = f"{name} must be greater than zero"
        raise ConfigurationError(message)
    return parsed


def _percentage(name: str) -> int:
    try:
        parsed = int(required_environment(name))
    except ValueError as exc:
        message = f"{name} must be an integer"
        raise ConfigurationError(message) from exc
    if not 1 <= parsed <= MAX_GPU_USAGE_PERCENT:
        message = f"{name} must be between 1 and 100"
        raise ConfigurationError(message)
    return parsed
