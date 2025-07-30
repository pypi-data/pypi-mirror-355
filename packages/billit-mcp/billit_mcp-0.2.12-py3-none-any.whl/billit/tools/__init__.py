from .account import router as account_router
from .accountant import router as accountant_router
from .ai_composite import router as ai_router
from .document import router as document_router
from .financial_transaction import router as financial_router
from .gl_account import router as gl_account_router
from .misc import router as misc_router
from .order import router as order_router
from .party import router as party_router
from .peppol import router as peppol_router
from .product import router as product_router
from .reports import router as reports_router
from .to_process import router as to_process_router
from .webhook import router as webhook_router

__all__ = [
    "party_router",
    "product_router",
    "order_router",
    "account_router",
    "financial_router",
    "accountant_router",
    "document_router",
    "gl_account_router",
    "to_process_router",
    "peppol_router",
    "misc_router",
    "reports_router",
    "webhook_router",
    "ai_router",
]
