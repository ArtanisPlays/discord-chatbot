import logging
import time

from domain.ports import LLMProvider

logger = logging.getLogger("ModelService")


class ModelService:
    """Use case: list/validate chat models and manage per-guild overrides."""

    MODELS_CACHE_TTL = 300  # seconds

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.guild_models: dict[int, str] = {}
        self._models_cache: list[dict] = []
        self._models_cached_at: float = 0.0

    def effective_model(self, guild_id: int | None) -> str:
        """The model active in a guild, or the provider's global default."""
        if guild_id and guild_id in self.guild_models:
            return self.guild_models[guild_id]
        return self.provider.model

    def set_guild_model(self, guild_id: int, model: str) -> None:
        self.guild_models[guild_id] = model

    def reset_guild_model(self, guild_id: int) -> None:
        self.guild_models.pop(guild_id, None)

    async def list_models(self) -> list[dict]:
        """Fetch available models, caching briefly to avoid hammering the API."""
        now = time.monotonic()
        if not self._models_cache or now - self._models_cached_at > self.MODELS_CACHE_TTL:
            self._models_cache = await self.provider.fetch_models()
            self._models_cached_at = now
        return self._models_cache
