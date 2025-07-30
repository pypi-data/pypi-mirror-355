"""FastAPI routes for Billit Party (contacts) endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient
from ..models.party import Party, PartyCreate, PartyUpdate

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Instantiate and return a Billit API client."""

    return BillitAPIClient()


@router.get("/parties")
async def list_parties(client: BillitAPIClient = Depends(get_client)) -> dict[str, Any]:
    """Retrieve a list of parties."""

    return await client.request("GET", "/parties")


@router.post("/parties")
async def create_party(
    party: PartyCreate, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Create a new party."""

    return await client.request("POST", "/parties", json=party.model_dump(by_alias=True))


@router.get("/parties/{party_id}")
async def get_party(
    party_id: int, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Retrieve a single party by ID."""

    return await client.request("GET", f"/parties/{party_id}")


@router.patch("/parties/{party_id}")
async def update_party(
    party_id: int, updates: PartyUpdate, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Apply partial updates to an existing party (customer/supplier).
    
    Supports updating all patchable fields including:
    - Contact info: Name, Email, Phone, Mobile, Fax
    - Address: Street, City, Zipcode, CountryCode, etc.
    - Business: VATNumber, IBAN, CommercialName
    - Accounting: GLAccountCode, VATLiable
    
    All fields are optional for PATCH operations.
    """
    return await client.request(
        "PATCH",
        f"/parties/{party_id}",
        json=updates.model_dump(exclude_none=True, by_alias=True),
    )


@router.patch("/parties/{party_id}/raw")
async def update_party_raw(
    party_id: int, 
    updates: dict[str, Any], 
    client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Apply raw partial updates to an existing party.
    
    Alternative endpoint that accepts a raw dict for maximum flexibility.
    Use PascalCase field names (e.g., "Email", "VATNumber", "ContactFirstName").
    
    Common fields: Name, Email, Phone, VATNumber, Street, City, Zipcode, 
    CountryCode, CommercialName, ContactFirstName, ContactLastName, etc.
    """
    ALLOWED_PATCH_FIELDS = {
        'Name', 'CommercialName', 'ContactFirstName', 'ContactLastName',
        'Email', 'Phone', 'Mobile', 'Fax', 'VATNumber', 'IBAN', 'Language',
        'CountryCode', 'City', 'Street', 'StreetNumber', 'Zipcode', 'Box',
        'VATLiable', 'GLAccountCode', 'GLDefaultExpiryOffset', 'Nr',
        'ExternalProviderTC', 'ExternalProviderID'
    }
    
    # Validate fields
    invalid_fields = set(updates.keys()) - ALLOWED_PATCH_FIELDS
    if invalid_fields:
        return {
            "success": False,
            "data": None,
            "error": f"Fields not patchable: {', '.join(invalid_fields)}. Allowed: {', '.join(sorted(ALLOWED_PATCH_FIELDS))}",
            "error_code": "INVALID_PATCH_FIELDS"
        }
    
    return await client.request("PATCH", f"/parties/{party_id}", json=updates)
