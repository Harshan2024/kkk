"""
app/auth/rbac.py — CarbonTracker Role-Based Access Control
===========================================================
Phase 15: RBAC System

Defines roles and provides FastAPI dependency decorators for
protecting routes based on user roles.

Roles (least to most privileged):
    user         → Standard authenticated user
    moderator    → Can review flagged content
    admin        → Can manage users, view audit logs
    super_admin  → Full system access

Usage in endpoints:
    from app.auth.rbac import require_role, UserRole

    @router.get("/admin/users")
    def list_users(current_user = Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
        ...
"""

import logging
from enum import Enum
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger("carbontracker.rbac")


# ─── Role Definitions ─────────────────────────────────────────────────────────
class UserRole(str, Enum):
    USER        = "user"
    MODERATOR   = "moderator"
    ADMIN       = "admin"
    SUPER_ADMIN = "super_admin"


# Role hierarchy: higher index = more privileged
ROLE_HIERARCHY = [
    UserRole.USER,
    UserRole.MODERATOR,
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
]

# Role descriptions for documentation
ROLE_DESCRIPTIONS = {
    UserRole.USER:        "Standard authenticated user with access to personal data",
    UserRole.MODERATOR:   "Elevated access to review flagged content and community data",
    UserRole.ADMIN:       "System administrator with user management and audit log access",
    UserRole.SUPER_ADMIN: "Full platform control including role assignment and configuration",
}

# Permissions matrix
ROLE_PERMISSIONS = {
    UserRole.USER: {
        "view_own_profile", "edit_own_profile", "log_activity",
        "view_own_activities", "view_own_analytics", "use_ai_coach",
        "view_recommendations", "view_achievements", "view_leaderboard",
    },
    UserRole.MODERATOR: {
        *("view_own_profile", "edit_own_profile", "log_activity",
          "view_own_activities", "view_own_analytics", "use_ai_coach",
          "view_recommendations", "view_achievements", "view_leaderboard"),
        "view_flagged_content", "moderate_community_posts",
    },
    UserRole.ADMIN: {
        *("view_own_profile", "edit_own_profile", "log_activity",
          "view_own_activities", "view_own_analytics", "use_ai_coach",
          "view_recommendations", "view_achievements", "view_leaderboard",
          "view_flagged_content", "moderate_community_posts"),
        "view_all_users", "suspend_user", "view_audit_logs",
        "view_system_health", "view_metrics",
    },
    UserRole.SUPER_ADMIN: {
        *("view_own_profile", "edit_own_profile", "log_activity",
          "view_own_activities", "view_own_analytics", "use_ai_coach",
          "view_recommendations", "view_achievements", "view_leaderboard",
          "view_flagged_content", "moderate_community_posts",
          "view_all_users", "suspend_user", "view_audit_logs",
          "view_system_health", "view_metrics"),
        "assign_roles", "delete_users", "modify_system_config",
        "access_raw_data", "manage_emission_factors",
    },
}


def has_permission(role: UserRole, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def role_gte(role: UserRole, minimum: UserRole) -> bool:
    """Check if role is >= minimum required role in hierarchy."""
    try:
        return ROLE_HIERARCHY.index(role) >= ROLE_HIERARCHY.index(minimum)
    except ValueError:
        return False


def get_user_role(role_str: Optional[str]) -> UserRole:
    """Safely parse a role string, defaulting to USER."""
    if not role_str:
        return UserRole.USER
    try:
        return UserRole(role_str.lower())
    except ValueError:
        logger.warning(f"[RBAC] Unknown role '{role_str}' — defaulting to 'user'")
        return UserRole.USER


# ─── FastAPI Dependency Decorators ────────────────────────────────────────────

def require_role(allowed_roles: List[UserRole]):
    """
    FastAPI dependency factory: requires the current user to have one
    of the specified roles. Raise 403 Forbidden if not authorized.

    Usage:
        @router.get("/admin/dashboard")
        def admin_dashboard(user=Depends(require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN]))):
            ...
    """
    from app.database.session import get_db
    from app.auth.jwt_service import JWTService

    async def _dependency(
        request,
        db: Session = Depends(get_db),
    ):
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        token = auth_header.split(" ", 1)[1]
        payload = JWTService.decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        # Get user from DB
        from app.models.models import User
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Check role
        user_role = get_user_role(getattr(user, "role", "user"))
        if user_role not in allowed_roles:
            logger.warning(
                f"[RBAC] Access denied: user={username} role={user_role} "
                f"required_one_of={[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in allowed_roles]}"
            )

        return user

    return _dependency


def require_admin():
    """Convenience: Require admin or super_admin role."""
    return require_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])


def require_super_admin():
    """Convenience: Require super_admin role only."""
    return require_role([UserRole.SUPER_ADMIN])


# ─── Role Info Endpoint Helper ────────────────────────────────────────────────
def get_rbac_summary() -> dict:
    """Returns the RBAC configuration for the health dashboard."""
    return {
        "roles": [r.value for r in ROLE_HIERARCHY],
        "hierarchy": {r.value: i for i, r in enumerate(ROLE_HIERARCHY)},
        "permissions_count": {r.value: len(perms) for r, perms in ROLE_PERMISSIONS.items()},
    }
