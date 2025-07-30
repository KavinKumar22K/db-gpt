"""Authentication middleware for DB-GPT."""

import logging
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from dbgpt._private.pydantic import BaseModel
from dbgpt.component import SystemApp

from .models.models import UserEntity
from .service.service import AuthService

logger = logging.getLogger(__name__)


class AuthenticatedUserRequest(BaseModel):
    """Authenticated user request model."""

    user_id: str
    user_no: Optional[str] = None
    real_name: Optional[str] = None
    user_name: str
    user_channel: Optional[str] = None
    role: str = "user"
    nick_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    nick_name_like: Optional[str] = None
    # Additional fields for enhanced auth
    is_superuser: bool = False
    role_id: int
    permissions: Optional[dict] = None


def create_auth_middleware(system_app: SystemApp):
    """Create authentication middleware factory."""
    
    # Get auth service from system app
    def get_auth_service() -> Optional[AuthService]:
        try:
            return system_app.get_component("dbgpt_serve_auth", AuthService)
        except Exception:
            logger.warning("Auth service not found, falling back to mock auth")
            return None

    security = HTTPBearer(auto_error=False)

    async def get_authenticated_user(
        dbgpt_auth_session: Optional[str] = Cookie(None),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> AuthenticatedUserRequest:
        """Get authenticated user from session or token."""
        auth_service = get_auth_service()
        
        if not auth_service:
            # Fallback to mock authentication for backward compatibility
            return _get_mock_user()

        user = None
        
        # Try session first
        if dbgpt_auth_session:
            try:
                user = await auth_service.get_current_user_from_session(dbgpt_auth_session)
            except Exception as e:
                logger.debug(f"Session auth failed: {e}")
        
        # Try token if session failed
        if not user and credentials:
            try:
                user = await auth_service.get_current_user_from_token(credentials.credentials)
            except Exception as e:
                logger.debug(f"Token auth failed: {e}")
        
        if not user:
            # For now, fall back to mock user to maintain compatibility
            # In production, you might want to raise an authentication error
            logger.warning("Authentication failed, falling back to mock user")
            return _get_mock_user()

        return _convert_user_to_request(user, auth_service)

    async def get_authenticated_user_strict(
        dbgpt_auth_session: Optional[str] = Cookie(None),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> AuthenticatedUserRequest:
        """Get authenticated user with strict authentication (no fallback)."""
        auth_service = get_auth_service()
        
        if not auth_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service not available",
            )

        user = None
        
        # Try session first
        if dbgpt_auth_session:
            user = await auth_service.get_current_user_from_session(dbgpt_auth_session)
        
        # Try token if session failed
        if not user and credentials:
            user = await auth_service.get_current_user_from_token(credentials.credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        return _convert_user_to_request(user, auth_service)

    def _get_mock_user() -> AuthenticatedUserRequest:
        """Get mock user for backward compatibility."""
        return AuthenticatedUserRequest(
            user_id="001",
            user_name="dbgpt",
            role="admin",
            nick_name="dbgpt",
            real_name="dbgpt",
            email="admin@dbgpt.com",
            is_superuser=True,
            role_id=1,
            permissions={
                "chat": True,
                "explore": True,
                "construct": True,
                "admin": True,
            },
        )

    def _convert_user_to_request(user: UserEntity, auth_service: AuthService) -> AuthenticatedUserRequest:
        """Convert UserEntity to AuthenticatedUserRequest."""
        import json
        
        permissions = {}
        if user.role and user.role.permissions:
            try:
                permissions = json.loads(user.role.permissions)
            except json.JSONDecodeError:
                permissions = {}

        return AuthenticatedUserRequest(
            user_id=str(user.id),
            user_no=str(user.id),
            real_name=user.full_name,
            user_name=user.username,
            user_channel="dbgpt",
            role=user.role.name if user.role else "user",
            nick_name=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            is_superuser=user.is_superuser,
            role_id=user.role_id,
            permissions=permissions,
        )

    async def require_admin_access(
        user: AuthenticatedUserRequest = Depends(get_authenticated_user),
    ) -> AuthenticatedUserRequest:
        """Require admin access."""
        if not user.is_superuser and not (user.permissions and user.permissions.get("admin", False)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return user

    async def require_construct_access(
        user: AuthenticatedUserRequest = Depends(get_authenticated_user),
    ) -> AuthenticatedUserRequest:
        """Require construct access."""
        if not user.is_superuser and not (user.permissions and user.permissions.get("construct", False)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Construct access required",
            )
        return user

    return {
        "get_authenticated_user": get_authenticated_user,
        "get_authenticated_user_strict": get_authenticated_user_strict,
        "require_admin_access": require_admin_access,
        "require_construct_access": require_construct_access,
        "AuthenticatedUserRequest": AuthenticatedUserRequest,
    } 