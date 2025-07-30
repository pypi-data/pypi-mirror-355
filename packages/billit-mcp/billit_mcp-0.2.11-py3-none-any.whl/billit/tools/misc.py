"""Miscellaneous utility routes."""

from typing import Any

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return the API client."""
    return BillitAPIClient()


@router.get("/search-company")
async def search_company(
    keywords: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Search for a company by keywords."""
    return await client.request("GET", f"/misc/companysearch/{keywords}")


@router.get("/type-codes/{code_type}")
async def get_type_codes(
    code_type: str, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Retrieve system code list."""
    return await client.request("GET", f"/misc/typecodes/{code_type}")


@router.get("/type-codes/{code_type}/{code_key}")
async def get_code_detail(
    code_type: str,
    code_key: str,
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Retrieve a single system code."""
    return await client.request("GET", f"/misc/typecodes/{code_type}/{code_key}")
