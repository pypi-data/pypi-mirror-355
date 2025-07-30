"""Routes for accountant feed endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return a Billit API client."""
    return BillitAPIClient()


@router.post("/feeds")
async def register_feed(
    data: dict[str, Any], client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Create a new feed subscription."""
    feed_data = {
        "FeedName": data.get("feed_name"),
        "FeedType": data.get("feed_type")
    }
    return await client.request("POST", "/feed", json=feed_data)


@router.get("/feeds")
async def list_feeds(client: BillitAPIClient = Depends(get_client)) -> dict[str, Any]:
    """List all registered feeds."""
    return await client.request("GET", "/feed")


@router.get("/feeds/{feed_name}")
async def get_feed_items(
    feed_name: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Retrieve pending items for a feed."""
    return await client.request("GET", f"/feed/{feed_name}")


@router.get("/feeds/{feed_name}/{item_id}")
async def download_feed_item_content(
    feed_name: str, item_id: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Download the file content of a feed item."""
    return await client.request("GET", f"/feed/{feed_name}/{item_id}")


@router.post("/feeds/{feed_name}/{item_id}/confirm")
async def confirm_feed_item(
    feed_name: str, item_id: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Mark a feed item as processed."""
    return await client.request("POST", f"/feed/{feed_name}/{item_id}/confirm")


@router.delete("/feeds/{feed_name}")
async def delete_feed(
    feed_name: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Delete a feed subscription."""
    return await client.request("DELETE", f"/feed/{feed_name}")
