"""FastAPI routes for Billit Order endpoints."""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends

from ..client import BillitAPIClient

router = APIRouter()


def get_client() -> BillitAPIClient:
    """Return a Billit API client instance."""
    return BillitAPIClient()


@router.get("/orders")
async def list_orders(
    odata_filter: Optional[str] = None,
    skip: int = 0,
    top: int = 120,
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Retrieve a list of orders."""
    params = {"$skip": skip, "$top": top}
    if odata_filter:
        params["$filter"] = odata_filter
    return await client.request("GET", "/orders", params=params)


@router.post("/orders")
async def create_order(
    order_data: dict[str, Any],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Create a new order."""
    return await client.request("POST", "/orders", json=order_data)


@router.get("/orders/deleted")
async def list_deleted_orders(
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Retrieve deleted orders for synchronization purposes."""
    return await client.request("GET", "/orders/deleted")


@router.get("/orders/{order_id}")
async def get_order(order_id: int, client: BillitAPIClient = Depends(get_client)) -> dict[str, Any]:
    """Retrieve a specific order by its ID."""
    return await client.request("GET", f"/orders/{order_id}")


@router.patch("/orders/{order_id}")
async def update_order(
    order_id: int,
    order_updates: dict[str, Any],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Update patchable properties of an existing order.
    
    IMPORTANT: Only these fields can be updated after order creation:
    - Paid, PaidDate, IsSent, ApprovalStatus, AccountCode, 
    - InternalInfo, Invoiced, AccountantVerificationNeeded
    
    CANNOT be updated after creation (requires new order):
    - VentilationCode (VAT classification like IC Services)
    - VATType, VAT percentages on OrderLines
    - Customer information, OrderLines content
    - OrderDate, ExpiryDate, Currency
    
    Use 'InternalInfo' field for comments/notes, not 'Comments'.
    """
    ALLOWED_PATCH_FIELDS = {
        'Paid', 'PaidDate', 'IsSent', 'ApprovalStatus', 
        'AccountCode', 'InternalInfo', 'Invoiced', 
        'AccountantVerificationNeeded'
    }
    
    # Validate fields
    invalid_fields = set(order_updates.keys()) - ALLOWED_PATCH_FIELDS
    if invalid_fields:
        return {
            "success": False,
            "data": None,
            "error": f"Fields not patchable: {', '.join(invalid_fields)}. Allowed: {', '.join(ALLOWED_PATCH_FIELDS)}. Use InternalInfo for comments.",
            "error_code": "INVALID_PATCH_FIELDS"
        }
    
    return await client.request("PATCH", f"/orders/{order_id}", json=order_updates)


@router.delete("/orders/{order_id}")
async def delete_order(order_id: int, client: BillitAPIClient = Depends(get_client)) -> dict[str, Any]:
    """Delete a draft order."""
    return await client.request("DELETE", f"/orders/{order_id}")


@router.post("/orders/{order_id}/payments")
async def record_payment(
    order_id: int,
    payment_info: dict[str, Any],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Record a payment for an order."""
    return await client.request("POST", f"/orders/{order_id}/payment", json=payment_info)


@router.post("/orders/send")
async def send_order(
    send_data: dict[str, Any],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Send one or more orders via specified transport.
    
    Expected JSON body format:
    {
        "order_ids": [123, 456],
        "transport_type": "SMTP",
        "strict_transport": false
    }
    
    Valid transport types:
    - SMTP: Email delivery (requires valid customer email)
    - Peppol: Peppol e-invoicing network
    - Letter: Physical mail
    - SDI: Italian network
    - KSeF: Polish network
    - OSA: Hungarian network
    - ANAF: Romanian network
    - SAT: Mexican network
    
    Important behaviors:
    - Peppol is tried first if customer is registered on network
    - If Peppol fails, fallback to email (unless strict_transport=true)
    - Email fallback requires valid customer email address
    - Set strict_transport=true to prevent fallbacks and enforce exact transport
    
    Common errors:
    - "TheCustomer_0_DoesNotHaveAValidEmailAddress": Update customer email first
    - Order must be in correct status (ToSend, not already Sent)
    
    Note: 'Email' auto-corrected to 'SMTP'
    """
    VALID_TRANSPORT_TYPES = {
        'SMTP', 'Peppol', 'Letter', 'SDI', 'KSeF', 'OSA', 'ANAF', 'SAT'
    }
    
    # Extract parameters from JSON body
    order_ids = send_data.get('order_ids', [])
    transport_type = send_data.get('transport_type', '')
    strict_transport = send_data.get('strict_transport', False)
    
    # Validate required fields
    if not order_ids:
        return {
            "success": False,
            "data": None,
            "error": "order_ids is required and must not be empty",
            "error_code": "MISSING_ORDER_IDS"
        }
    
    if not transport_type:
        return {
            "success": False,
            "data": None,
            "error": "transport_type is required",
            "error_code": "MISSING_TRANSPORT_TYPE"
        }
    
    # Auto-correct common mistakes
    if transport_type == "Email":
        transport_type = "SMTP"
    
    # Validate transport type
    if transport_type not in VALID_TRANSPORT_TYPES:
        return {
            "success": False,
            "data": None,
            "error": f"Invalid transport type '{transport_type}'. Valid types: {', '.join(VALID_TRANSPORT_TYPES)}. Use 'SMTP' for email.",
            "error_code": "INVALID_TRANSPORT_TYPE"
        }
    
    # Prepare data for Billit API
    data = {
        "Transporttype": transport_type,
        "OrderIDs": order_ids,
    }
    
    # Add the StrictTransportType header if requested
    headers = {}
    if strict_transport:
        headers["StrictTransportType"] = "true"
    
    return await client.request("POST", "/orders/commands/send", json=data, **({'headers': headers} if headers else {}))


@router.post("/orders/{order_id}/booking")
async def add_booking_entries(
    order_id: int,
    entries: list[dict[str, Any]],
    client: BillitAPIClient = Depends(get_client),
) -> dict[str, Any]:
    """Add booking entries to an order."""
    return await client.request("POST", f"/orders/{order_id}/booking", json=entries)
