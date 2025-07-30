"""Authentication service for DB-GPT."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import jwt
from fastapi import HTTPException, Request, status

from dbgpt.component import SystemApp
from dbgpt.storage.metadata import DatabaseManager

from ..config import ServeConfig
from ..models.models import (
    RoleDao,
    RoleEntity,
    SessionDao,
    SessionEntity,
    UserDao,
    UserDatabaseAccessDao,
    UserEntity,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""

    def __init__(self, system_app: SystemApp, config: Optional[ServeConfig] = None):
        self._system_app = system_app
        self._config = config or ServeConfig()
        self._db_manager: Optional[DatabaseManager] = None
        self._user_dao: Optional[UserDao] = None
        self._role_dao: Optional[RoleDao] = None
        self._session_dao: Optional[SessionDao] = None
        self._user_db_access_dao: Optional[UserDatabaseAccessDao] = None

    def init_db(self, db_manager: DatabaseManager):
        """Initialize database components."""
        self._db_manager = db_manager
        self._user_dao = UserDao(db_manager)
        self._role_dao = RoleDao(db_manager)
        self._session_dao = SessionDao(db_manager)
        self._user_db_access_dao = UserDatabaseAccessDao(db_manager)

    async def initialize_default_data(self):
        """Initialize default roles and admin user."""
        if not self._role_dao or not self._user_dao:
            raise RuntimeError("Database not initialized")

        # Create default roles
        user_role = self._role_dao.get_by_name("user")
        if not user_role:
            user_permissions = json.dumps({
                "chat": True,
                "explore": True,
                "construct": False,
                "admin": False,
            })
            user_role = RoleEntity(
                name="user",
                description="Regular user with chat and explore access",
                permissions=user_permissions,
            )
            user_role = self._role_dao.create(user_role)

        admin_role = self._role_dao.get_by_name("admin")
        if not admin_role:
            admin_permissions = json.dumps({
                "chat": True,
                "explore": True,
                "construct": True,
                "admin": True,
            })
            admin_role = RoleEntity(
                name="admin",
                description="Administrator with full access",
                permissions=admin_permissions,
            )
            admin_role = self._role_dao.create(admin_role)

        # Create default admin user
        admin_user = self._user_dao.get_by_username(self._config.default_admin_username)
        if not admin_user:
            admin_user = UserEntity(
                username=self._config.default_admin_username,
                email=self._config.default_admin_email,
                full_name="Administrator",
                is_superuser=True,
                role_id=admin_role.id,
            )
            admin_user.set_password(self._config.default_admin_password)
            admin_user = self._user_dao.create(admin_user)
            logger.info(f"Created default admin user: {admin_user.username}")

    def _generate_jwt_token(self, user: UserEntity) -> str:
        """Generate JWT token for user."""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "is_superuser": user.is_superuser,
            "exp": datetime.utcnow() + timedelta(seconds=self._config.jwt_expire_time),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(
            payload, self._config.jwt_secret_key, algorithm=self._config.jwt_algorithm
        )

    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token, self._config.jwt_secret_key, algorithms=[self._config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[UserEntity]]:
        """Register a new user."""
        if not self._user_dao or not self._role_dao:
            return False, "Authentication service not initialized", None

        # Validate password
        if len(password) < self._config.password_min_length:
            return False, f"Password must be at least {self._config.password_min_length} characters long", None

        # Check if username already exists
        existing_user = self._user_dao.get_by_username(username)
        if existing_user:
            return False, "Username already exists", None

        # Check if email already exists
        existing_email = self._user_dao.get_by_email(email)
        if existing_email:
            return False, "Email already exists", None

        # Get default user role
        user_role = self._role_dao.get_by_name("user")
        if not user_role:
            return False, "Default user role not found", None

        # Create new user
        new_user = UserEntity(
            username=username,
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            role_id=user_role.id,
        )
        new_user.set_password(password)

        try:
            created_user = self._user_dao.create(new_user)
            logger.info(f"Registered new user: {created_user.username}")
            return True, "User registered successfully", created_user
        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            return False, "Failed to register user", None

    async def authenticate_user(
        self, username: str, password: str, request: Optional[Request] = None
    ) -> Tuple[bool, str, Optional[UserEntity], Optional[str]]:
        """Authenticate user and return JWT token."""
        if not self._user_dao or not self._session_dao:
            return False, "Authentication service not initialized", None, None

        # Get user by username
        user = self._user_dao.get_by_username(username)
        if not user:
            return False, "Invalid username or password", None, None

        # Check if user is active
        if not user.is_active:
            return False, "User account is disabled", None, None

        # Verify password
        if not user.check_password(password):
            return False, "Invalid username or password", None, None

        # Generate JWT token
        jwt_token = self._generate_jwt_token(user)

        # Create session
        user_agent = request.headers.get("User-Agent") if request else None
        ip_address = request.client.host if request and request.client else None
        
        session = SessionEntity.create_session(
            user_id=user.id,
            jwt_token=jwt_token,
            expire_time=self._config.session_expire_time,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        try:
            created_session = self._session_dao.create(session)
            
            # Update last login
            user.last_login = datetime.now()
            self._user_dao.update(user)
            
            logger.info(f"User {user.username} authenticated successfully")
            return True, "Authentication successful", user, created_session.session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False, "Failed to create session", None, None

    async def logout_user(self, session_id: str) -> Tuple[bool, str]:
        """Logout user by deactivating session."""
        if not self._session_dao:
            return False, "Authentication service not initialized"

        try:
            success = self._session_dao.deactivate_session(session_id)
            if success:
                logger.info(f"Session {session_id} deactivated")
                return True, "Logout successful"
            else:
                return False, "Session not found"
        except Exception as e:
            logger.error(f"Failed to logout user: {e}")
            return False, "Failed to logout"

    async def get_current_user_from_session(self, session_id: str) -> Optional[UserEntity]:
        """Get current user from session ID."""
        if not self._session_dao or not self._user_dao:
            return None

        session = self._session_dao.get_by_session_id(session_id)
        if not session or session.is_expired():
            return None

        # Verify JWT token
        payload = self._verify_jwt_token(session.jwt_token)
        if not payload:
            # Deactivate invalid session
            self._session_dao.deactivate_session(session_id)
            return None

        # Get user
        user = self._user_dao.get_by_id(session.user_id)
        if not user or not user.is_active:
            return None

        return user

    async def get_current_user_from_token(self, token: str) -> Optional[UserEntity]:
        """Get current user from JWT token."""
        if not self._user_dao:
            return None

        payload = self._verify_jwt_token(token)
        if not payload:
            return None

        user = self._user_dao.get_by_id(payload["user_id"])
        if not user or not user.is_active:
            return None

        return user

    def has_permission(self, user: UserEntity, permission: str) -> bool:
        """Check if user has specific permission."""
        if user.is_superuser:
            return True

        if not user.role or not user.role.permissions:
            return False

        try:
            permissions = json.loads(user.role.permissions)
            return permissions.get(permission, False)
        except (json.JSONDecodeError, AttributeError):
            return False

    def can_access_construct(self, user: UserEntity) -> bool:
        """Check if user can access construct functionality."""
        return self.has_permission(user, "construct")

    def can_access_admin(self, user: UserEntity) -> bool:
        """Check if user can access admin functionality."""
        return self.has_permission(user, "admin")

    def can_access_database(self, user: UserEntity, db_name: str) -> bool:
        """Check if user has access to specific database."""
        if user.is_superuser:
            return True

        if not self._user_db_access_dao:
            return False

        return self._user_db_access_dao.has_database_access(user.id, db_name)

    async def grant_database_access(
        self, admin_user: UserEntity, user_id: int, db_name: str
    ) -> Tuple[bool, str]:
        """Grant database access to user (admin only)."""
        if not self.can_access_admin(admin_user):
            return False, "Admin access required"

        if not self._user_db_access_dao:
            return False, "Database access service not initialized"

        try:
            # Check if access already exists
            if self._user_db_access_dao.has_database_access(user_id, db_name):
                return False, "User already has access to this database"

            self._user_db_access_dao.grant_database_access(
                user_id=user_id, db_name=db_name, granted_by=admin_user.id
            )
            logger.info(f"Admin {admin_user.username} granted database access for {db_name} to user {user_id}")
            return True, "Database access granted successfully"
            
        except Exception as e:
            logger.error(f"Failed to grant database access: {e}")
            return False, "Failed to grant database access"

    async def revoke_database_access(
        self, admin_user: UserEntity, user_id: int, db_name: str
    ) -> Tuple[bool, str]:
        """Revoke database access from user (admin only)."""
        if not self.can_access_admin(admin_user):
            return False, "Admin access required"

        if not self._user_db_access_dao:
            return False, "Database access service not initialized"

        try:
            success = self._user_db_access_dao.revoke_database_access(user_id, db_name)
            if success:
                logger.info(f"Admin {admin_user.username} revoked database access for {db_name} from user {user_id}")
                return True, "Database access revoked successfully"
            else:
                return False, "User does not have access to this database"
                
        except Exception as e:
            logger.error(f"Failed to revoke database access: {e}")
            return False, "Failed to revoke database access"

    async def get_user_databases(self, user: UserEntity) -> List[str]:
        """Get list of databases accessible by user."""
        if user.is_superuser:
            # Superuser has access to all databases - would need to query actual DB list
            return []  # Return empty for now, could be enhanced to return all DBs

        if not self._user_db_access_dao:
            return []

        accesses = self._user_db_access_dao.get_user_databases(user.id)
        return [access.db_name for access in accesses]

    async def get_all_users(self, admin_user: UserEntity) -> List[UserEntity]:
        """Get all users (admin only)."""
        if not self.can_access_admin(admin_user):
            return []

        if not self._user_dao:
            return []

        return self._user_dao.get_active_users()

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        if not self._session_dao:
            return 0

        try:
            count = self._session_dao.cleanup_expired_sessions()
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0 