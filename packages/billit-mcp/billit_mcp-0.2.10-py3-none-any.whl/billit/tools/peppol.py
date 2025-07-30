"""Routes for Billit Peppol endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return the API client."""
    return BillitAPIClient()


@router.get("/peppol/participantInformation/{identifier}")
async def check_peppol_participant(
    identifier: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Check if a company is registered on Peppol."""
    return await client.request("GET", f"/peppol/participantInformation/{identifier}")


@router.post("/peppol/participants")
async def register_peppol_participant(
    data: dict[str, Any], client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Register the current company on Peppol."""
    return await client.request("POST", "/peppol/participants", json=data)


@router.delete("/peppol/participants")
async def unregister_peppol_participant(
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Unregister the company from Peppol."""
    return await client.request("DELETE", "/peppol/participants")


@router.post("/peppol/sendOrder")
async def send_peppol_invoice(
    order_id: int, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Send an order via the Peppol network."""
    return await client.request("POST", "/peppol/sendOrder", json={"order_id": order_id})


@router.get("/peppol/inbox")
async def list_peppol_inbox(
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Retrieve incoming e-invoices."""
    return await client.request("GET", "/peppol/inbox")


@router.post("/peppol/inbox/{inbox_item_id}/confirm")
async def confirm_peppol_invoice(
    inbox_item_id: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Confirm an incoming e-invoice."""
    return await client.request("POST", f"/peppol/inbox/{inbox_item_id}/confirm")


@router.post("/peppol/inbox/{inbox_item_id}/refuse")
async def refuse_peppol_invoice(
    inbox_item_id: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Refuse an incoming e-invoice."""
    return await client.request("POST", f"/peppol/inbox/{inbox_item_id}/refuse")
