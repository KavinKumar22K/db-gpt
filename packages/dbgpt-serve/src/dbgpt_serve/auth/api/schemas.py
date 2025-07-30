"""API schemas for authentication service."""

from typing import List, Optional

from dbgpt._private.pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Login response schema."""

    success: bool = Field(..., description="Login success status")
    message: str = Field(..., description="Response message")
    session_id: Optional[str] = Field(None, description="Session ID")
    user: Optional["UserResponse"] = Field(None, description="User information")


class RegisterRequest(BaseModel):
    """Register request schema."""

    username: str = Field(..., description="Username", min_length=3, max_length=128)
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password", min_length=8)
    full_name: Optional[str] = Field(None, description="Full name", max_length=255)
    avatar_url: Optional[str] = Field(None, description="Avatar URL", max_length=512)


class RegisterResponse(BaseModel):
    """Register response schema."""

    success: bool = Field(..., description="Registration success status")
    message: str = Field(..., description="Response message")
    user: Optional["UserResponse"] = Field(None, description="Created user information")


class LogoutRequest(BaseModel):
    """Logout request schema."""

    session_id: str = Field(..., description="Session ID to logout")


class LogoutResponse(BaseModel):
    """Logout response schema."""

    success: bool = Field(..., description="Logout success status")
    message: str = Field(..., description="Response message")


class UserResponse(BaseModel):
    """User response schema."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_active: bool = Field(..., description="Is user active")
    is_superuser: bool = Field(..., description="Is superuser")
    role_id: int = Field(..., description="Role ID")
    role_name: Optional[str] = Field(None, description="Role name")
    last_login: Optional[str] = Field(None, description="Last login time")
    gmt_created: Optional[str] = Field(None, description="Creation time")


class RoleResponse(BaseModel):
    """Role response schema."""

    id: int = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: Optional[str] = Field(None, description="Permissions JSON")
    gmt_created: Optional[str] = Field(None, description="Creation time")


class DatabaseAccessRequest(BaseModel):
    """Database access request schema."""

    user_id: int = Field(..., description="User ID")
    db_name: str = Field(..., description="Database name")


class DatabaseAccessResponse(BaseModel):
    """Database access response schema."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")


class UserDatabaseAccessResponse(BaseModel):
    """User database access response schema."""

    id: int = Field(..., description="Access ID")
    user_id: int = Field(..., description="User ID")
    db_name: str = Field(..., description="Database name")
    granted_by: int = Field(..., description="Granted by user ID")
    is_active: bool = Field(..., description="Is access active")
    gmt_created: Optional[str] = Field(None, description="Creation time")


class UserListResponse(BaseModel):
    """User list response schema."""

    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")


class UserDatabaseListResponse(BaseModel):
    """User database list response schema."""

    databases: List[str] = Field(..., description="List of accessible databases")
    total: int = Field(..., description="Total number of databases")


class CurrentUserResponse(BaseModel):
    """Current user response schema."""

    user: Optional[UserResponse] = Field(None, description="Current user information")
    permissions: Optional[dict] = Field(None, description="User permissions")
    accessible_databases: List[str] = Field([], description="Accessible databases")


# Update forward references
LoginResponse.model_rebuild()
RegisterResponse.model_rebuild() 