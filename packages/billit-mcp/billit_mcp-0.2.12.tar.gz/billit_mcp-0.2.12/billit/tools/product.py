"""FastAPI routes for Billit Product endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient
from ..models.product import ProductUpsert

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Instantiate and return a Billit API client."""

    return BillitAPIClient()


@router.get("/products")
async def list_products(
    odata_filter: Optional[str] = None,
    skip: int = 0,
    top: int = 120,
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """List products with optional OData filter and pagination."""

    params = {"$skip": skip, "$top": top}
    if odata_filter:
        params["$filter"] = odata_filter
    return await client.request("GET", "/products", params=params)


@router.get("/products/{product_id}")
async def get_product(
    product_id: int, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Fetch a single product by ID."""

    return await client.request("GET", f"/products/{product_id}")


@router.post("/products")
async def upsert_product(
    product: ProductUpsert, client: BillitAPIClient = Depends(get_client)
) -> dict[str, Any]:
    """Create or update a product."""

    data = product.model_dump(exclude_none=True, by_alias=True)
    return await client.request("POST", "/products", json=data)
