"""FastAPI dependencies for the activia-trace application.

Public dependencies:
    - get_db: async session per request
    - get_tenant: resolves current tenant_id
    - get_settings: cached Settings instance
    - get_current_user: resolves identity from JWT
    - require_2fa: gates 2FA-required endpoints
    - require_permission: RBAC guard factory
"""

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.current_user import get_current_user, require_2fa
from app.core.permission_guard import require_permission
from app.core.tenancy import get_tenant

# Re-export as the canonical dependency name
get_db = get_db_session
