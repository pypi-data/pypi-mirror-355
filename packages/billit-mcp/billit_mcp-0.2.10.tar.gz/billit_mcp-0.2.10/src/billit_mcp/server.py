#!/usr/bin/env python3
"""Billit MCP Server - Model Context Protocol server for Billit API integration."""

import os
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from billit.client import BillitAPIClient

# Initialize the MCP server
mcp = FastMCP("billit-mcp", dependencies=["httpx", "pydantic", "python-dotenv"])


# Dependency to get the API client
async def get_client() -> BillitAPIClient:
    """Get configured Billit API client."""
    return BillitAPIClient()


# Party Management Tools
@mcp.tool()
async def list_parties(
    party_type: str,
    odata_filter: Optional[str] = None,
    skip: int = 0,
    top: int = 120
) -> Dict[str, Any]:
    """List parties (customers or suppliers).
    
    Args:
        party_type: Type of party - 'Customer' or 'Supplier'
        odata_filter: Optional OData filter expression
        skip: Number of records to skip for pagination
        top: Maximum number of records to return (max 120)
    """
    client = await get_client()
    params = {
        "PartyType": party_type,
        "$skip": skip,
        "$top": top
    }
    if odata_filter:
        params["$filter"] = odata_filter
    
    return await client.request("GET", "/parties", params=params)


@mcp.tool()
async def create_party(party_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new party (customer or supplier).
    
    Args:
        party_data: Party data including Name, PartyType, VAT number, etc.
    """
    client = await get_client()
    return await client.request("POST", "/parties", json=party_data)


@mcp.tool()
async def get_party(party_id: int) -> Dict[str, Any]:
    """Get details of a specific party.
    
    Args:
        party_id: The ID of the party to retrieve
    """
    client = await get_client()
    return await client.request("GET", f"/parties/{party_id}")


@mcp.tool()
async def update_party(party_id: int, party_updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing party.
    
    Args:
        party_id: The ID of the party to update
        party_updates: Fields to update
    """
    client = await get_client()
    return await client.request("PATCH", f"/parties/{party_id}", json=party_updates)


# Product Management Tools
@mcp.tool()
async def list_products(
    odata_filter: Optional[str] = None,
    skip: int = 0,
    top: int = 120
) -> Dict[str, Any]:
    """List products.
    
    Args:
        odata_filter: Optional OData filter expression
        skip: Number of records to skip for pagination
        top: Maximum number of records to return (max 120)
    """
    client = await get_client()
    params = {"$skip": skip, "$top": top}
    if odata_filter:
        params["$filter"] = odata_filter
    
    return await client.request("GET", "/products", params=params)


@mcp.tool()
async def get_product(product_id: int) -> Dict[str, Any]:
    """Get details of a specific product.
    
    Args:
        product_id: The ID of the product to retrieve
    """
    client = await get_client()
    return await client.request("GET", f"/products/{product_id}")


@mcp.tool()
async def upsert_product(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a product.
    
    Args:
        product_data: Product data including Description, UnitPrice, VAT rate, etc.
    """
    client = await get_client()
    return await client.request("POST", "/products", json=product_data)


# Order Management Tools
@mcp.tool()
async def list_orders(
    odata_filter: Optional[str] = None,
    skip: int = 0,
    top: int = 120
) -> Dict[str, Any]:
    """List orders (invoices, credit notes, etc.).
    
    Args:
        odata_filter: Optional OData filter expression
        skip: Number of records to skip for pagination
        top: Maximum number of records to return (max 120)
    """
    client = await get_client()
    params = {"$skip": skip, "$top": top}
    if odata_filter:
        params["$filter"] = odata_filter
    
    return await client.request("GET", "/orders", params=params)


@mcp.tool()
async def create_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new order (invoice, credit note, etc.).
    
    Args:
        order_data: Order data including Customer, OrderLines, etc.
    """
    client = await get_client()
    return await client.request("POST", "/orders", json=order_data)


@mcp.tool()
async def get_order(order_id: int) -> Dict[str, Any]:
    """Get details of a specific order.
    
    Args:
        order_id: The ID of the order to retrieve
    """
    client = await get_client()
    return await client.request("GET", f"/orders/{order_id}")


@mcp.tool()
async def update_order(order_id: int, order_updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing order.
    
    Args:
        order_id: The ID of the order to update
        order_updates: Fields to update (Paid, PaidDate, IsSent, etc.)
    """
    client = await get_client()
    return await client.request("PATCH", f"/orders/{order_id}", json=order_updates)


@mcp.tool()
async def delete_order(order_id: int) -> Dict[str, Any]:
    """Delete a draft order.
    
    Args:
        order_id: The ID of the order to delete
    """
    client = await get_client()
    return await client.request("DELETE", f"/orders/{order_id}")


@mcp.tool()
async def record_payment(order_id: int, payment_info: Dict[str, Any]) -> Dict[str, Any]:
    """Record a payment for an order.
    
    Args:
        order_id: The ID of the order
        payment_info: Payment details including amount, date, etc.
    """
    client = await get_client()
    return await client.request("POST", f"/orders/{order_id}/payment", json=payment_info)


@mcp.tool()
async def send_order(
    order_ids: List[int],
    transport_type: str,
    strict_transport: bool = False
) -> Dict[str, Any]:
    """Send one or more orders via specified transport.
    
    Args:
        order_ids: List of order IDs to send
        transport_type: Transport method ('Peppol', 'Email', etc.)
        strict_transport: If True, prevent fallback to email
    """
    client = await get_client()
    data = {
        "order_ids": order_ids,
        "transport_type": transport_type,
        "strict_transport": strict_transport
    }
    return await client.request("POST", "/orders/send", json=data)


@mcp.tool()
async def add_booking_entries(order_id: int, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add booking entries to an order.
    
    Args:
        order_id: The ID of the order
        entries: List of booking entries
    """
    client = await get_client()
    return await client.request("POST", f"/orders/{order_id}/booking", json=entries)


@mcp.tool()
async def list_deleted_orders() -> Dict[str, Any]:
    """List recently deleted orders."""
    client = await get_client()
    return await client.request("GET", "/orders/deleted")


# Financial Transaction Tools
@mcp.tool()
async def list_financial_transactions(
    odata_filter: Optional[str] = None,
    skip: int = 0,
    top: int = 120
) -> Dict[str, Any]:
    """List financial transactions.
    
    Args:
        odata_filter: Optional OData filter expression
        skip: Number of records to skip for pagination
        top: Maximum number of records to return (max 120)
    """
    client = await get_client()
    params = {"$skip": skip, "$top": top}
    if odata_filter:
        params["$filter"] = odata_filter
    
    return await client.request("GET", "/financialTransactions", params=params)


@mcp.tool()
async def import_transactions_file(file_path: str) -> Dict[str, Any]:
    """Import a bank statement file.
    
    Args:
        file_path: Path to the file to import (CODA, CSV, etc.)
    """
    client = await get_client()
    return await client.request("POST", "/financialTransactions/importFile", json={"file_path": file_path})


@mcp.tool()
async def confirm_transaction_import(import_id: str) -> Dict[str, Any]:
    """Confirm a transaction import.
    
    Args:
        import_id: The ID of the import to confirm
    """
    client = await get_client()
    return await client.request("POST", f"/financialTransactions/commands/import", json={"import_id": import_id})


# Account Management Tools
@mcp.tool()
async def get_account_information() -> Dict[str, Any]:
    """Get information about the authenticated account."""
    client = await get_client()
    return await client.request("GET", "/account/accountInformation")


@mcp.tool()
async def get_sso_token() -> Dict[str, Any]:
    """Get a Single Sign-On token for the Billit web UI."""
    client = await get_client()
    return await client.request("GET", "/account/ssoToken")


@mcp.tool()
async def get_next_sequence_number(sequence_type: str, consume: bool = False) -> Dict[str, Any]:
    """Get the next sequence number.
    
    Args:
        sequence_type: Type of sequence (e.g., 'Income-Invoice')
        consume: If True, consume the number
    """
    client = await get_client()
    data = {"sequence_type": sequence_type, "consume": consume}
    return await client.request("POST", "/account/sequences", json=data)


@mcp.tool()
async def register_company(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new company (for accountants).
    
    Args:
        company_data: Company registration data
    """
    client = await get_client()
    return await client.request("POST", "/account/registercompany", json=company_data)


# Document Management Tools
@mcp.tool()
async def list_documents(
    odata_filter: Optional[str] = None,
    skip: int = 0,
    top: int = 120
) -> Dict[str, Any]:
    """List documents.
    
    Args:
        odata_filter: Optional OData filter expression
        skip: Number of records to skip for pagination
        top: Maximum number of records to return (max 120)
    """
    client = await get_client()
    params = {"$skip": skip, "$top": top}
    if odata_filter:
        params["$filter"] = odata_filter
    
    return await client.request("GET", "/documents", params=params)


@mcp.tool()
async def upload_document(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Upload a document.
    
    Args:
        file_path: Path to the file to upload
        metadata: Document metadata
    """
    client = await get_client()
    data = {"file_path": file_path, "metadata": metadata}
    return await client.request("POST", "/documents", json=data)


@mcp.tool()
async def get_document(document_id: int) -> Dict[str, Any]:
    """Get details of a specific document.
    
    Args:
        document_id: The ID of the document to retrieve
    """
    client = await get_client()
    return await client.request("GET", f"/documents/{document_id}")


@mcp.tool()
async def download_file(file_id: str) -> Dict[str, Any]:
    """Download a file.
    
    Args:
        file_id: The ID of the file to download
    """
    client = await get_client()
    return await client.request("GET", f"/files/{file_id}")


# Webhook Management Tools
@mcp.tool()
async def create_webhook(url: str, entity_type: str, update_type: str) -> Dict[str, Any]:
    """Create a webhook subscription.
    
    Args:
        url: The webhook URL
        entity_type: Type of entity to subscribe to
        update_type: Type of updates to receive
    """
    client = await get_client()
    data = {
        "url": url,
        "entity_type": entity_type,
        "update_type": update_type
    }
    return await client.request("POST", "/webhook", json=data)


@mcp.tool()
async def list_webhooks() -> Dict[str, Any]:
    """List all configured webhooks."""
    client = await get_client()
    return await client.request("GET", "/webhook")


@mcp.tool()
async def delete_webhook(webhook_id: str) -> Dict[str, Any]:
    """Delete a webhook subscription.
    
    Args:
        webhook_id: The ID of the webhook to delete
    """
    client = await get_client()
    return await client.request("DELETE", f"/webhook/{webhook_id}")


@mcp.tool()
async def refresh_webhook_secret(webhook_id: str) -> Dict[str, Any]:
    """Refresh the signing secret for a webhook.
    
    Args:
        webhook_id: The ID of the webhook
    """
    client = await get_client()
    return await client.request("POST", f"/webhook/{webhook_id}/refresh")


# Peppol E-invoicing Tools
@mcp.tool()
async def check_peppol_participant(identifier: str) -> Dict[str, Any]:
    """Check if a company is a Peppol participant.
    
    Args:
        identifier: Company identifier (VAT, CBE, GLN, etc.)
    """
    client = await get_client()
    return await client.request("GET", f"/peppol/participantInformation/{identifier}")


@mcp.tool()
async def register_peppol_participant(registration_data: Dict[str, Any]) -> Dict[str, Any]:
    """Register as a Peppol participant.
    
    Args:
        registration_data: Registration information
    """
    client = await get_client()
    return await client.request("POST", "/peppol/participants", json=registration_data)


@mcp.tool()
async def send_peppol_invoice(order_id: int) -> Dict[str, Any]:
    """Send an invoice via Peppol.
    
    Args:
        order_id: The ID of the order to send
    """
    client = await get_client()
    return await client.request("POST", "/peppol/sendOrder", json={"order_id": order_id})


# AI Composite Tools
@mcp.tool()
async def suggest_payment_reconciliation() -> Dict[str, Any]:
    """Get AI-powered payment reconciliation suggestions."""
    client = await get_client()
    return await client.request("GET", "/ai/suggest-payment-reconciliation")


@mcp.tool()
async def generate_invoice_summary(start_date: str, end_date: str) -> Dict[str, Any]:
    """Generate an AI-powered invoice summary.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    client = await get_client()
    params = {"start_date": start_date, "end_date": end_date}
    return await client.request("GET", "/ai/invoice-summary", params=params)


@mcp.tool()
async def list_overdue_invoices() -> Dict[str, Any]:
    """List all overdue invoices."""
    client = await get_client()
    return await client.request("GET", "/ai/overdue-invoices")


@mcp.tool()
async def get_cashflow_overview(period: str) -> Dict[str, Any]:
    """Get a cashflow overview for a period.
    
    Args:
        period: Period specification (e.g., '2024-Q1', '2024-01')
    """
    client = await get_client()
    params = {"period": period}
    return await client.request("GET", "/ai/cashflow", params=params)


# Utility Tools
@mcp.tool()
async def search_company(keywords: str) -> Dict[str, Any]:
    """Search for a company by name or number.
    
    Args:
        keywords: Search keywords
    """
    client = await get_client()
    return await client.request("GET", f"/misc/companysearch/{keywords}")


@mcp.tool()
async def get_type_codes(code_type: str) -> Dict[str, Any]:
    """Get available codes for a type.
    
    Args:
        code_type: Type of codes (e.g., 'VATRate', 'Currency', 'OrderStatus')
    """
    client = await get_client()
    return await client.request("GET", f"/misc/typecodes/{code_type}")


@mcp.tool()
async def list_available_reports() -> Dict[str, Any]:
    """List all available report types."""
    client = await get_client()
    return await client.request("GET", "/reports")


@mcp.tool()
async def get_report(report_id: str, **params) -> Dict[str, Any]:
    """Generate and download a report.
    
    Args:
        report_id: The ID of the report type
        **params: Additional report parameters (depends on report type)
    """
    client = await get_client()
    return await client.request("GET", f"/reports/{report_id}", params=params)