"""Routes for Billit OCR processing queue."""

from typing import Any

from fastapi import APIRouter, Depends, UploadFile, Form
import json

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return the Billit client."""
    return BillitAPIClient()


@router.post("/process")
async def submit_document_for_processing(
    file: UploadFile,
    metadata: str = Form(...),
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Upload a document for OCR processing."""
    files = {"file": (file.filename, await file.read())}
    # Parse the metadata JSON string
    metadata_dict = json.loads(metadata)
    return await client.request("POST", "/toProcess", files=files, data=metadata_dict)


@router.patch("/process/{upload_id}")
async def update_processing_request(
    upload_id: str,
    data: dict[str, Any],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Update an in-progress processing request."""
    return await client.request("PATCH", f"/toProcess/{upload_id}", json=data)


@router.delete("/process/{upload_id}")
async def cancel_processing_request(
    upload_id: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Cancel a processing request."""
    return await client.request("DELETE", f"/toProcess/{upload_id}")
