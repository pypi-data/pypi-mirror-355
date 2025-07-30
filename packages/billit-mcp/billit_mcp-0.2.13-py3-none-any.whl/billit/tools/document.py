"""Routes for document and file management."""

from typing import Any

from fastapi import APIRouter, Depends, UploadFile, Form
import json

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return a Billit API client."""
    return BillitAPIClient()


@router.get("/documents")
async def list_documents(
    odata_filter: str | None = None,
    skip: int = 0,
    top: int = 120,
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """List documents."""
    params = {"$skip": skip, "$top": top}
    if odata_filter:
        params["$filter"] = odata_filter
    return await client.request("GET", "/documents", params=params)


@router.post("/documents")
async def upload_document(
    file: UploadFile,
    metadata: str = Form(...),
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Upload a file as a document."""
    files = {"file": (file.filename, await file.read())}
    # Parse the metadata JSON string
    metadata_dict = json.loads(metadata)
    return await client.request("POST", "/documents", files=files, data=metadata_dict)


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Retrieve a document's metadata."""
    return await client.request("GET", f"/documents/{document_id}")


@router.get("/files/{file_id}")
async def download_file(
    file_id: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Download file content from Billit."""
    return await client.request("GET", f"/files/{file_id}")
