from datetime import timedelta

from pydantic import HttpUrl, TypeAdapter

from collective_compute.gateway.registry import ProviderRegistry
from collective_compute.gateway.schemas import ProviderRegistration, ProviderStatus


def registration(node_id: str = "node-a", gpu_usage: int = 50) -> ProviderRegistration:
    return ProviderRegistration(
        node_id=node_id,
        endpoint_url=TypeAdapter(HttpUrl).validate_python(f"http://{node_id}.example.com"),
        gpu_name="RTX 4090",
        vram_gb=24,
        max_gpu_usage_percent=gpu_usage,
    )


def test_registry_selects_online_provider_with_highest_capacity() -> None:
    registry = ProviderRegistry()
    _ = registry.register(registration("node-a", 50))
    _ = registry.register(registration("node-b", 80))

    selected = registry.available_provider()
    assert selected is not None
    assert selected.node_id == "node-b"


def test_stale_provider_is_offline_and_not_selected() -> None:
    registry = ProviderRegistry(heartbeat_timeout_seconds=1)
    provider = registry.register(registration())
    provider.last_heartbeat_at -= timedelta(seconds=2)

    assert registry.available_provider() is None
    assert provider.status == ProviderStatus.OFFLINE


def test_heartbeat_restores_registered_provider_to_online() -> None:
    registry = ProviderRegistry(heartbeat_timeout_seconds=1)
    provider = registry.register(registration())
    provider.last_heartbeat_at -= timedelta(seconds=2)
    _ = registry.all_providers()

    result = registry.heartbeat("node-a")

    assert result is provider
    assert result is not None
    assert result.status == ProviderStatus.ONLINE
