"""HTTP client for interacting with the Billit REST API."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def get_env(name: str, default: Optional[str] = None) -> str:
    """Return the value of an environment variable or raise if missing."""

    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


@dataclass
class RateLimiter:
    """Simple token bucket rate limiter for outgoing requests."""

    rate_per_minute: int

    def __post_init__(self) -> None:
        """Initialize token bucket state."""

        self._tokens = self.rate_per_minute
        self._lock = asyncio.Lock()
        self._last_refill = time.monotonic()

    async def acquire(self) -> None:
        """Wait until a token is available."""

        async with self._lock:
            await self._refill()
            while self._tokens <= 0:
                await asyncio.sleep(1)
                await self._refill()
            self._tokens -= 1

    async def _refill(self) -> None:
        """Refill tokens based on elapsed time."""

        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_refill
        tokens_to_add = int(elapsed / 60 * self.rate_per_minute)
        if tokens_to_add > 0:
            self._tokens = min(self.rate_per_minute, self._tokens + tokens_to_add)
            self._last_refill = now


class BillitAPIClient:
    """Thin wrapper around ``httpx.AsyncClient`` with rate limiting and response handling."""

    def __init__(self) -> None:
        """Initialize the client using environment variables for configuration."""

        self.base_url = get_env("BILLIT_BASE_URL")
        self.api_key = get_env("BILLIT_API_KEY")
        self.party_id = get_env("BILLIT_PARTY_ID")
        self.context_party_id = os.getenv("BILLIT_CONTEXT_PARTY_ID")  # Optional for accountants
        self.rate_limiter = RateLimiter(int(os.getenv("RATE_LIMIT_PER_MINUTE", "50")))
        
        # Set up headers with correct case
        headers = {
            "apiKey": self.api_key,
            "partyID": self.party_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add context party ID if available (for accountants)
        if self.context_party_id:
            headers["ContextPartyID"] = self.context_party_id
            
        self.client = httpx.AsyncClient(
            base_url=self.base_url, headers=headers
        )

    async def request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """Perform a request against the Billit API and wrap the response."""

        await self.rate_limiter.acquire()
        response = await self.client.request(method, url, **kwargs)
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: httpx.Response) -> dict[str, Any]:
        """Convert a raw HTTP response into the MCP envelope."""

        if response.status_code // 100 == 2:
            data = response.json()
            return {"success": True, "data": data, "error": None, "error_code": None}
        try:
            payload = response.json()
        except Exception:
            payload = {}
        error = payload.get("errors") or payload.get("message") or response.text
        error_code = payload.get("code")
        return {
            "success": False,
            "data": None,
            "error": error,
            "error_code": error_code,
        }

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        await self.client.aclose()
