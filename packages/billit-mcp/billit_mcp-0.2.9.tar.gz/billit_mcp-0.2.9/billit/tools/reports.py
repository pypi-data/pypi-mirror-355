"""Routes for Billit report generation."""

from typing import Any

from fastapi import APIRouter, Depends, Request

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return the API client."""
    return BillitAPIClient()


@router.get("/reports")
async def list_available_reports(
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """List all report types."""
    return await client.request("GET", "/report")


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str, 
    request: Request,
    client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Retrieve a specific report."""
    # Pass through any query parameters
    params = dict(request.query_params)
    return await client.request("GET", f"/report/{report_id}", params=params)
