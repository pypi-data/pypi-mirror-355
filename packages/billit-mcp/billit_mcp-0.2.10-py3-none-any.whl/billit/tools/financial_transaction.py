"""Routes for Billit financial transaction endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, UploadFile

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return a Billit API client instance."""
    return BillitAPIClient()


@router.get("/financial-transactions")
async def list_financial_transactions(
    odata_filter: str | None = None,
    skip: int = 0,
    top: int = 120,
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Retrieve bank transactions."""
    params = {"$skip": skip, "$top": top}
    if odata_filter:
        params["$filter"] = odata_filter
    return await client.request("GET", "/financialTransactions", params=params)


@router.post("/financial-transactions/import")
async def import_transactions_file(
    file: UploadFile,
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Upload a bank statement file."""
    files = {"file": (file.filename, await file.read())}
    return await client.request("POST", "/financialTransactions/importFile", files=files)


@router.post("/financial-transactions/{import_id}/confirm")
async def confirm_transaction_import(
    import_id: str,
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Confirm a transaction file import."""
    return await client.request("POST", "/financialTransactions/commands/import")
