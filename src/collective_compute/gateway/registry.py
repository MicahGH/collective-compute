from datetime import UTC, datetime, timedelta

from .schemas import ProviderRecord, ProviderRegistration, ProviderStatus


class ProviderRegistry:
    """In-memory provider store; replaceable with a PostgreSQL-backed implementation."""

    def __init__(self, heartbeat_timeout_seconds: int = 60) -> None:
        """Initialize the registry with its provider heartbeat timeout."""
        self._providers: dict[str, ProviderRecord] = {}
        self._heartbeat_timeout = timedelta(seconds=heartbeat_timeout_seconds)

    def register(self, registration: ProviderRegistration) -> ProviderRecord:
        """Create or replace a provider record and mark it online."""
        record = ProviderRecord(
            **registration.model_dump(),
            status=ProviderStatus.ONLINE,
            last_heartbeat_at=self._now(),
        )
        self._providers[record.node_id] = record
        return record

    def heartbeat(self, node_id: str) -> ProviderRecord | None:
        """Refresh a registered provider's heartbeat, if it exists."""
        provider = self._providers.get(node_id)
        if provider is None:
            return None
        provider.last_heartbeat_at = self._now()
        provider.status = ProviderStatus.ONLINE
        return provider

    def available_provider(self) -> ProviderRecord | None:
        """Return the highest-capacity online provider, if one is available."""
        self._mark_stale_providers_offline()
        candidates = [p for p in self._providers.values() if p.status == ProviderStatus.ONLINE]
        if not candidates:
            return None
        return max(candidates, key=lambda p: (p.max_gpu_usage_percent, p.vram_gb))

    def all_providers(self) -> list[ProviderRecord]:
        """Return all providers after refreshing stale statuses."""
        self._mark_stale_providers_offline()
        return list(self._providers.values())

    def _mark_stale_providers_offline(self) -> None:
        cutoff = self._now() - self._heartbeat_timeout
        for provider in self._providers.values():
            if provider.last_heartbeat_at < cutoff:
                provider.status = ProviderStatus.OFFLINE

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
