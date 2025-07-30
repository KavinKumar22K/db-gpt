"""Configuration for the auth service."""

from dbgpt._private.pydantic import BaseModel, Field
from dbgpt_serve.core.config import BaseServeConfig

APP_NAME = "auth"
SERVE_APP_NAME = "dbgpt_serve_auth"
SERVE_APP_NAME_HUMP = "dbgpt-serve-auth"
SERVE_CONFIG_KEY_PREFIX = "dbgpt.serve.auth"
SERVER_APP_TABLE_NAME = "dbgpt_serve_auth"

# Additional table names for auth service
USER_TABLE_NAME = "dbgpt_serve_auth_users"
ROLE_TABLE_NAME = "dbgpt_serve_auth_roles" 
USER_DATABASE_ACCESS_TABLE_NAME = "dbgpt_serve_auth_user_db_access"
SESSION_TABLE_NAME = "dbgpt_serve_auth_sessions"


class ServeConfig(BaseServeConfig):
    """Configuration for the auth service."""

    # JWT Configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token generation",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT token generation",
    )
    jwt_expire_time: int = Field(
        default=24 * 60 * 60,  # 24 hours in seconds
        description="JWT token expiration time in seconds",
    )
    
    # Session Configuration
    session_expire_time: int = Field(
        default=30 * 24 * 60 * 60,  # 30 days in seconds
        description="Session expiration time in seconds",
    )
    
    # Password Configuration
    password_min_length: int = Field(
        default=8,
        description="Minimum password length",
    )
    
    # Default admin user configuration
    default_admin_username: str = Field(
        default="admin",
        description="Default admin username",
    )
    default_admin_password: str = Field(
        default="dbgpt2024",
        description="Default admin password",
    )
    default_admin_email: str = Field(
        default="admin@dbgpt.com",
        description="Default admin email",
    ) 