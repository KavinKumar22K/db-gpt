"""API endpoints for authentication service."""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from dbgpt.component import SystemApp
from dbgpt_serve.core import Result

from ..config import ServeConfig
from ..service.service import AuthService
from .schemas import (
    CurrentUserResponse,
    DatabaseAccessRequest,
    DatabaseAccessResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    RegisterRequest,
    RegisterResponse,
    UserDatabaseListResponse,
    UserListResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

global_system_app: Optional[SystemApp] = None
global_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the auth service instance."""
    if not global_auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized",
        )
    return global_auth_service


security = HTTPBearer(auto_error=False)


async def get_current_user_from_session(
    dbgpt_auth_session: Optional[str] = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current user from session cookie."""
    if not dbgpt_auth_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = await auth_service.get_current_user_from_session(dbgpt_auth_session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return user


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = await auth_service.get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user


async def get_current_user(
    dbgpt_auth_session: Optional[str] = Cookie(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current user from session or token."""
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

    return user


async def require_admin_user(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Require admin user."""
    if not auth_service.can_access_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.post("/register", response_model=Result[RegisterResponse])
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user."""
    try:
        success, message, user = await auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            avatar_url=request.avatar_url,
        )

        user_response = None
        if user:
            user_response = UserResponse(**user.to_dict())

        response = RegisterResponse(
            success=success,
            message=message,
            user=user_response,
        )

        if success:
            return Result.succ(response)
        else:
            return Result.failed(response.message, response)

    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return Result.failed("Registration failed", RegisterResponse(
            success=False,
            message="Internal server error",
            user=None,
        ))


@router.post("/login", response_model=Result[LoginResponse])
async def login(
    request: LoginRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login user."""
    try:
        success, message, user, session_id = await auth_service.authenticate_user(
            username=request.username,
            password=request.password,
            request=http_request,
        )

        user_response = None
        if user:
            user_response = UserResponse(**user.to_dict())

        response = LoginResponse(
            success=success,
            message=message,
            session_id=session_id,
            user=user_response,
        )

        if success:
            result = Result.succ(response)
            # Set session cookie
            if session_id:
                # Note: In a real implementation, you'd set the cookie in the response
                # This is handled by the frontend calling code
                pass
            return result
        else:
            return Result.failed(response.message, response)

    except Exception as e:
        logger.error(f"Login failed: {e}")
        return Result.failed("Login failed", LoginResponse(
            success=False,
            message="Internal server error",
            session_id=None,
            user=None,
        ))


@router.post("/logout", response_model=Result[LogoutResponse])
async def logout(
    request: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout user."""
    try:
        success, message = await auth_service.logout_user(request.session_id)

        response = LogoutResponse(
            success=success,
            message=message,
        )

        if success:
            return Result.succ(response)
        else:
            return Result.failed(response.message, response)

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return Result.failed("Logout failed", LogoutResponse(
            success=False,
            message="Internal server error",
        ))


@router.get("/me", response_model=Result[CurrentUserResponse])
async def get_current_user_info(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current user information."""
    try:
        user_response = UserResponse(**current_user.to_dict())
        
        # Get user permissions
        permissions = {}
        if current_user.role and current_user.role.permissions:
            try:
                permissions = json.loads(current_user.role.permissions)
            except json.JSONDecodeError:
                permissions = {}

        # Get accessible databases
        accessible_databases = await auth_service.get_user_databases(current_user)

        response = CurrentUserResponse(
            user=user_response,
            permissions=permissions,
            accessible_databases=accessible_databases,
        )

        return Result.succ(response)

    except Exception as e:
        logger.error(f"Failed to get current user info: {e}")
        return Result.failed("Failed to get user information")


@router.get("/users", response_model=Result[UserListResponse])
async def get_users(
    admin_user = Depends(require_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get all users (admin only)."""
    try:
        users = await auth_service.get_all_users(admin_user)
        user_responses = [UserResponse(**user.to_dict()) for user in users]

        response = UserListResponse(
            users=user_responses,
            total=len(user_responses),
        )

        return Result.succ(response)

    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return Result.failed("Failed to get users")


@router.post("/database-access/grant", response_model=Result[DatabaseAccessResponse])
async def grant_database_access(
    request: DatabaseAccessRequest,
    admin_user = Depends(require_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Grant database access to user (admin only)."""
    try:
        success, message = await auth_service.grant_database_access(
            admin_user=admin_user,
            user_id=request.user_id,
            db_name=request.db_name,
        )

        response = DatabaseAccessResponse(
            success=success,
            message=message,
        )

        if success:
            return Result.succ(response)
        else:
            return Result.failed(response.message, response)

    except Exception as e:
        logger.error(f"Failed to grant database access: {e}")
        return Result.failed("Failed to grant database access", DatabaseAccessResponse(
            success=False,
            message="Internal server error",
        ))


@router.post("/database-access/revoke", response_model=Result[DatabaseAccessResponse])
async def revoke_database_access(
    request: DatabaseAccessRequest,
    admin_user = Depends(require_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Revoke database access from user (admin only)."""
    try:
        success, message = await auth_service.revoke_database_access(
            admin_user=admin_user,
            user_id=request.user_id,
            db_name=request.db_name,
        )

        response = DatabaseAccessResponse(
            success=success,
            message=message,
        )

        if success:
            return Result.succ(response)
        else:
            return Result.failed(response.message, response)

    except Exception as e:
        logger.error(f"Failed to revoke database access: {e}")
        return Result.failed("Failed to revoke database access", DatabaseAccessResponse(
            success=False,
            message="Internal server error",
        ))


@router.get("/database-access", response_model=Result[UserDatabaseListResponse])
async def get_user_database_access(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get user's accessible databases."""
    try:
        databases = await auth_service.get_user_databases(current_user)

        response = UserDatabaseListResponse(
            databases=databases,
            total=len(databases),
        )

        return Result.succ(response)

    except Exception as e:
        logger.error(f"Failed to get user database access: {e}")
        return Result.failed("Failed to get database access")


def init_endpoints(system_app: SystemApp, config: ServeConfig):
    """Initialize endpoints with system app and config."""
    global global_system_app, global_auth_service
    global_system_app = system_app
    
    # Initialize auth service
    from dbgpt.storage.metadata import UnifiedDBManagerFactory
    
    db_manager = system_app.get_component(UnifiedDBManagerFactory)
    global_auth_service = AuthService(system_app, config)
    global_auth_service.init_db(db_manager)
    
    # Initialize default data
    async def _init_default_data():
        await global_auth_service.initialize_default_data()
    
    # Schedule initialization after system startup
    system_app.register_instance(global_auth_service)
    
    # Add cleanup task for expired sessions
    async def cleanup_sessions():
        if global_auth_service:
            await global_auth_service.cleanup_expired_sessions()
    
    # Note: In production, you'd want to run cleanup_sessions periodically 