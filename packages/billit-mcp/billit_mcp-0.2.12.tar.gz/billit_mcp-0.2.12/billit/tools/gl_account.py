"""Routes for GL account and journal entries."""

from typing import Any, List

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return the API client."""
    return BillitAPIClient()


@router.post("/gl-accounts")
async def create_gl_account(
    account_data: dict[str, Any], client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Create a single GL account."""
    return await client.request("POST", "/glAccount", json=account_data)


@router.post("/gl-accounts/import")
async def import_gl_accounts(
    accounts_data: List[dict[str, Any]],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Import multiple GL accounts."""
    return await client.request("POST", "/glAccount/import", json=accounts_data)


@router.post("/journal-entries/import")
async def import_journal_entries(
    entries_data: List[dict[str, Any]],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Import journal entries."""
    return await client.request("POST", "/journalEntry/import", json=entries_data)
