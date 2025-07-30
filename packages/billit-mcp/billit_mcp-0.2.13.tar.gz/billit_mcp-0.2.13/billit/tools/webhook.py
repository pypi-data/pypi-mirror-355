"""Routes for Billit webhook management."""

from typing import Any

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return the API client."""
    return BillitAPIClient()


@router.post("/webhooks")
async def create_webhook(
    webhook_data: dict[str, Any],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Create a new webhook subscription."""
    data = {
        "Url": webhook_data["url"],
        "EntityType": webhook_data["entity_type"],
        "UpdateType": webhook_data["update_type"],
    }
    return await client.request("POST", "/webhook", json=data)


@router.get("/webhooks")
async def list_webhooks(
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Retrieve configured webhooks."""
    return await client.request("GET", "/webhook")


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Delete a webhook subscription."""
    return await client.request("DELETE", f"/webhook/{webhook_id}")


@router.post("/webhooks/{webhook_id}/refresh-secret")
async def refresh_webhook_secret(
    webhook_id: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Refresh a webhook signing secret."""
    return await client.request("POST", f"/webhook/{webhook_id}/refreshsecret")
