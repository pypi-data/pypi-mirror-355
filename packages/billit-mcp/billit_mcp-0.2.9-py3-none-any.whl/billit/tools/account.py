"""FastAPI routes for Billit Account endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient
from ..models.account import CompanyRegister

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return a Billit API client."""
    return BillitAPIClient()


@router.get("/account")
async def get_account_information(
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Retrieve account details."""
    return await client.request("GET", "/account/accountInformation")


@router.get("/account/sso")
async def get_sso_token(
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Retrieve a single sign-on token."""
    return await client.request("GET", "/account/ssoToken")


@router.get("/account/sequence/{sequence_type}")
async def get_next_sequence_number(
    sequence_type: str,
    consume: bool = False,
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Get the next number for a sequence."""
    data = {"sequence_type": sequence_type, "consume": consume}
    return await client.request("POST", "/account/sequences", json=data)


@router.post("/account/register")
async def register_company(
    company: CompanyRegister, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Register a company under the authenticated account."""
    return await client.request("POST", "/account/registercompany", json=company.model_dump())
