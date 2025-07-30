# Billit MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to the Billit API for invoice management, financial transactions, and e-invoicing.

[![Add to Cursor](https://img.shields.io/badge/Add%20to%20Cursor-5865F2?style=for-the-badge&logo=cursor&logoColor=white)](cursor://anysphere.cursor-deeplink/mcp/install?name=billit-mcp&config=eyJjb21tYW5kIjoicGlweCIsImFyZ3MiOlsicnVuIiwiLS1zcGVjIiwiYmlsbGl0LW1jcD09MC4yLjYiLCJweXRob24iLCItbSIsImJpbGxpdF9tY3AiXSwiZW52Ijp7IkJJTExJVF9BUElfS0VZIjoiIiwiQklMTElUX0JBU0VfVVJMIjoiaHR0cHM6Ly9hcGkuYmlsbGl0LmJlL3YxIiwiQklMTElUX1BBUlRZX0lEIjoiIiwiQklMTElUX0NPTlRFWFRfUEFSVFlfSUQiOiIifX0%3D)

**Copy this URL to add to Cursor (Auto-Update with pipx):**
```
cursor://anysphere.cursor-deeplink/mcp/install?name=billit-mcp&config=eyJjb21tYW5kIjoicGlweCIsImFyZ3MiOlsicnVuIiwiLS1zcGVjIiwiYmlsbGl0LW1jcD09MC4yLjYiLCJweXRob24iLCItbSIsImJpbGxpdF9tY3AiXSwiZW52Ijp7IkJJTExJVF9BUElfS0VZIjoiIiwiQklMTElUX0JBU0VfVVJMIjoiaHR0cHM6Ly9hcGkuYmlsbGl0LmJlL3YxIiwiQklMTElUX1BBUlRZX0lEIjoiIiwiQklMTElUX0NPTlRFWFRfUEFSVFlfSUQiOiIifX0%3D
```

## Overview

This MCP server provides 66 tools across 15 domains of the Billit API, enabling AI assistants to:

- 📄 Create and manage invoices, credit notes, and quotes
- 👥 Manage customers and suppliers
- 📦 Handle product catalogs
- 💰 Track financial transactions
- 📧 Send invoices via email or Peppol e-invoicing
- 🪝 Configure webhooks for real-time updates
- 🤖 Use AI-powered tools for reconciliation and analysis
- 📊 Generate financial reports

## Quick Start

### Option 1: One-Click Installation (Recommended)

Click the "Add to Cursor" button above to automatically configure the server in Cursor.

### Option 2: Install from PyPI

```bash
pip install billit-mcp
```

Then add to Cursor manually:
- Open Cursor Settings → MCP → "Add new MCP server"
- Enter server name: `billit-mcp`
- Enter command: `python -m billit_mcp`
- Add your environment variables

> 💡 **Auto-Update Available**: Want to always run the latest version? Use the pipx configuration - see [AUTO-UPDATE.md](AUTO-UPDATE.md) for details.

### Option 3: Manual Installation

1. **Clone and install**:
   ```bash
   git clone https://github.com/markov-kernel/Billit-mcp.git
   cd Billit-mcp
   ./setup.sh  # or manually: poetry install
   ```

2. **Configure your environment**:
   Create a `.env` file with your Billit credentials:
   ```env
   BILLIT_API_KEY=your-api-key
   BILLIT_BASE_URL=https://api.billit.be/v1
   BILLIT_PARTY_ID=your-party-id
   BILLIT_CONTEXT_PARTY_ID=  # Optional, for accountant use
   ```

3. **Add to Cursor manually**:
   - Open Cursor Settings → MCP → "Add new MCP server"
   - Enter the server name: `billit-mcp`
   - Enter the command: `python -m billit_mcp`
   - Add the environment variables from your `.env` file

## Getting Started with Billit

1. **Create a Billit Production Account**:
   - Register at [https://my.billit.be/Account/Register](https://my.billit.be/Account/Register)
   - This gives you access to the production environment

2. **Find Your Credentials**:
   - **API Key**: Profile → Users & API Key
   - **Party ID**: Navigate to "My Company" and find the ID in the URL (e.g., `.../Company/Edit/12345`)

## Available Tools

### Core Business Operations

#### Party Management (4 tools)
- `list_parties` - List customers or suppliers with filtering
- `create_party` - Create new customers/suppliers
- `get_party` - Get detailed party information
- `update_party` - Update party details

#### Order Management (9 tools)
- `list_orders` - List invoices, credit notes, quotes
- `create_order` - Create new invoices/orders
- `get_order` - Get order details
- `update_order` - Update order properties
- `delete_order` - Delete draft orders
- `record_payment` - Record payments
- `send_order` - Send via email/Peppol
- `add_booking_entries` - Add accounting entries
- `list_deleted_orders` - Track deleted orders

#### Product Management (3 tools)
- `list_products` - Browse product catalog
- `get_product` - Get product details
- `upsert_product` - Create/update products

### Financial Operations

#### Financial Transactions (3 tools)
- `list_financial_transactions` - View bank transactions
- `import_transactions_file` - Import bank statements
- `confirm_transaction_import` - Confirm imports

#### Account Management (4 tools)
- `get_account_information` - Account details
- `get_sso_token` - Single sign-on access
- `get_next_sequence_number` - Invoice numbering
- `register_company` - Register new companies

### Document & Communication

#### Document Management (4 tools)
- `list_documents` - Browse documents
- `upload_document` - Upload files
- `get_document` - Get document metadata
- `download_file` - Download files

#### Webhook Management (4 tools)
- `create_webhook` - Subscribe to events
- `list_webhooks` - View subscriptions
- `delete_webhook` - Remove webhooks
- `refresh_webhook_secret` - Rotate secrets

#### Peppol E-invoicing (7 tools)
- `check_peppol_participant` - Verify Peppol status
- `register_peppol_participant` - Join Peppol network
- `send_peppol_invoice` - Send e-invoices
- Plus 4 more tools for inbox management

### AI-Powered Tools (11 tools)
- `suggest_payment_reconciliation` - Match payments to invoices
- `generate_invoice_summary` - Period summaries
- `list_overdue_invoices` - Track late payments
- `get_cashflow_overview` - Financial insights
- Plus 7 more AI analysis tools

### Additional Domains
- **Accountant Tools** (6 tools) - Feed management
- **GL Account Tools** (3 tools) - Chart of accounts
- **OCR Processing** (3 tools) - Document processing
- **Reporting** (2 tools) - Financial reports
- **Miscellaneous** (3 tools) - Company search, system codes

## Example Usage in Cursor

Once installed, you can ask the AI assistant to:

- "Create an invoice for customer 'Tech Corp' for €5,000 of consulting services"
- "List all overdue invoices and suggest which ones to follow up on"
- "Check if company VAT BE0123456789 is on the Peppol network"
- "Generate a summary of this month's sales"
- "Import this bank statement and match transactions to invoices"

## Development

### Running the MCP Server Locally
```bash
# Activate environment and run
poetry shell
python -m billit_mcp
```

### Running Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=billit

# Run live integration tests (requires credentials)
poetry run pytest tests/test_live_integration.py --live
```

### Running the FastAPI Server (Legacy)
```bash
# Development server with auto-reload
poetry run uvicorn server:app --reload

# Production server
poetry run uvicorn server:app --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -t billit-mcp .
docker run --env-file .env -p 8000:8000 billit-mcp
```

## Project Structure
```
billit-mcp/
├── src/
│   └── billit_mcp/
│       ├── __init__.py
│       └── server.py      # MCP server implementation
├── billit/
│   ├── client.py          # API client with rate limiting
│   ├── models/            # Pydantic models
│   └── tools/             # FastAPI routers (legacy)
├── tests/                 # Comprehensive test suite
├── mcp.json              # MCP configuration
└── pyproject.toml        # Package configuration
```

## Features

- 🔒 **Secure**: API key authentication with environment variables
- ⚡ **Rate Limited**: Built-in rate limiting to respect API limits
- 🧪 **Well Tested**: 87% test coverage with comprehensive test suite
- 📚 **Documented**: All tools have detailed descriptions and parameter documentation
- 🔄 **Async**: Full async/await support for optimal performance
- 🎯 **Type Safe**: Full type annotations with Pydantic models

## Environment Variables

```env
# Required
BILLIT_API_KEY="your-api-key"
BILLIT_BASE_URL="https://api.billit.be/v1"
BILLIT_PARTY_ID="your-party-id"

# Optional
BILLIT_CONTEXT_PARTY_ID=""  # For accountant use cases
RATE_LIMIT_PER_MINUTE=50    # Default: 50
MCP_SERVER_PORT=8000        # Default: 8000
LOG_LEVEL="INFO"            # Default: INFO
```

## Support

- **Billit API Documentation**: See `billit_docs_markdown/` directory
- **MCP Documentation**: [Model Context Protocol](https://modelcontextprotocol.io)
- **Issues**: [GitHub Issues](https://github.com/markov-kernel/Billit-mcp/issues)

## License

This project is licensed under the MIT License.