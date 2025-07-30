"""Database models for authentication and authorization."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from dbgpt.storage.metadata import BaseDao, Model

from ..config import (
    ROLE_TABLE_NAME,
    SESSION_TABLE_NAME,
    USER_DATABASE_ACCESS_TABLE_NAME,
    USER_TABLE_NAME,
    ServeConfig,
)


class UserEntity(Model):
    """User entity for authentication."""

    __tablename__ = USER_TABLE_NAME
    __table_args__ = (
        UniqueConstraint("username", name="uk_username"),
        UniqueConstraint("email", name="uk_email"),
    )

    id = Column(Integer, primary_key=True, comment="Auto increment id")
    username = Column(String(128), nullable=False, comment="Username")
    email = Column(String(255), nullable=False, comment="Email address")
    password_hash = Column(String(255), nullable=False, comment="Password hash")
    salt = Column(String(64), nullable=False, comment="Password salt")
    full_name = Column(String(255), nullable=True, comment="Full name")
    avatar_url = Column(String(512), nullable=True, comment="Avatar URL")
    is_active = Column(Boolean, default=True, comment="Is user active")
    is_superuser = Column(Boolean, default=False, comment="Is superuser")
    role_id = Column(
        Integer, ForeignKey(f"{ROLE_TABLE_NAME}.id"), nullable=False, comment="Role ID"
    )
    last_login = Column(DateTime, nullable=True, comment="Last login time")
    gmt_created = Column(DateTime, default=datetime.now, comment="Record creation time")
    gmt_modified = Column(DateTime, default=datetime.now, comment="Record update time")

    # Relationships
    role = relationship("RoleEntity", back_populates="users")
    database_accesses = relationship("UserDatabaseAccessEntity", back_populates="user")
    sessions = relationship("SessionEntity", back_populates="user")

    def set_password(self, password: str) -> None:
        """Set password with salt and hash."""
        self.salt = secrets.token_hex(32)
        self.password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.salt.encode("utf-8"), 100000
        ).hex()

    def check_password(self, password: str) -> bool:
        """Check if provided password matches the stored hash."""
        if not self.salt or not self.password_hash:
            return False
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.salt.encode("utf-8"), 100000
        ).hex()
        return password_hash == self.password_hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "role_id": self.role_id,
            "role_name": self.role.name if self.role else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "gmt_created": self.gmt_created.isoformat() if self.gmt_created else None,
        }


class RoleEntity(Model):
    """Role entity for role-based access control."""

    __tablename__ = ROLE_TABLE_NAME
    __table_args__ = (UniqueConstraint("name", name="uk_role_name"),)

    id = Column(Integer, primary_key=True, comment="Auto increment id")
    name = Column(String(64), nullable=False, comment="Role name")
    description = Column(String(255), nullable=True, comment="Role description")
    permissions = Column(Text, nullable=True, comment="Permissions JSON")
    gmt_created = Column(DateTime, default=datetime.now, comment="Record creation time")
    gmt_modified = Column(DateTime, default=datetime.now, comment="Record update time")

    # Relationships
    users = relationship("UserEntity", back_populates="role")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "gmt_created": self.gmt_created.isoformat() if self.gmt_created else None,
        }


class UserDatabaseAccessEntity(Model):
    """User database access permissions."""

    __tablename__ = USER_DATABASE_ACCESS_TABLE_NAME
    __table_args__ = (
        UniqueConstraint("user_id", "db_name", name="uk_user_db_access"),
    )

    id = Column(Integer, primary_key=True, comment="Auto increment id")
    user_id = Column(
        Integer, ForeignKey(f"{USER_TABLE_NAME}.id"), nullable=False, comment="User ID"
    )
    db_name = Column(String(255), nullable=False, comment="Database name")
    granted_by = Column(
        Integer, ForeignKey(f"{USER_TABLE_NAME}.id"), nullable=False, comment="Granted by user ID"
    )
    is_active = Column(Boolean, default=True, comment="Is access active")
    gmt_created = Column(DateTime, default=datetime.now, comment="Record creation time")
    gmt_modified = Column(DateTime, default=datetime.now, comment="Record update time")

    # Relationships
    user = relationship("UserEntity", foreign_keys=[user_id], back_populates="database_accesses")
    granted_by_user = relationship("UserEntity", foreign_keys=[granted_by])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "db_name": self.db_name,
            "granted_by": self.granted_by,
            "is_active": self.is_active,
            "gmt_created": self.gmt_created.isoformat() if self.gmt_created else None,
        }


class SessionEntity(Model):
    """User session entity."""

    __tablename__ = SESSION_TABLE_NAME

    id = Column(Integer, primary_key=True, comment="Auto increment id")
    session_id = Column(String(255), unique=True, nullable=False, comment="Session ID")
    user_id = Column(
        Integer, ForeignKey(f"{USER_TABLE_NAME}.id"), nullable=False, comment="User ID"
    )
    jwt_token = Column(Text, nullable=False, comment="JWT token")
    expires_at = Column(DateTime, nullable=False, comment="Session expiration time")
    is_active = Column(Boolean, default=True, comment="Is session active")
    user_agent = Column(String(512), nullable=True, comment="User agent")
    ip_address = Column(String(45), nullable=True, comment="IP address")
    gmt_created = Column(DateTime, default=datetime.now, comment="Record creation time")
    gmt_modified = Column(DateTime, default=datetime.now, comment="Record update time")

    # Relationships
    user = relationship("UserEntity", back_populates="sessions")

    @classmethod
    def create_session(
        cls,
        user_id: int,
        jwt_token: str,
        expire_time: int,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> "SessionEntity":
        """Create a new session."""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=expire_time)
        
        return cls(
            session_id=session_id,
            user_id=user_id,
            jwt_token=jwt_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "gmt_created": self.gmt_created.isoformat() if self.gmt_created else None,
        }


class UserDao(BaseDao[UserEntity, Dict[str, Any], Dict[str, Any]]):
    """User DAO."""

    def get_by_username(self, username: str) -> Optional[UserEntity]:
        """Get user by username."""
        with self.session(commit=False) as session:
            return session.query(UserEntity).filter_by(username=username).first()

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email."""
        with self.session(commit=False) as session:
            return session.query(UserEntity).filter_by(email=email).first()

    def get_active_users(self) -> List[UserEntity]:
        """Get all active users."""
        with self.session(commit=False) as session:
            return session.query(UserEntity).filter_by(is_active=True).all()


class RoleDao(BaseDao[RoleEntity, Dict[str, Any], Dict[str, Any]]):
    """Role DAO."""

    def get_by_name(self, name: str) -> Optional[RoleEntity]:
        """Get role by name."""
        with self.session(commit=False) as session:
            return session.query(RoleEntity).filter_by(name=name).first()


class UserDatabaseAccessDao(BaseDao[UserDatabaseAccessEntity, Dict[str, Any], Dict[str, Any]]):
    """User database access DAO."""

    def get_user_databases(self, user_id: int) -> List[UserDatabaseAccessEntity]:
        """Get all databases accessible by user."""
        with self.session(commit=False) as session:
            return (
                session.query(UserDatabaseAccessEntity)
                .filter_by(user_id=user_id, is_active=True)
                .all()
            )

    def has_database_access(self, user_id: int, db_name: str) -> bool:
        """Check if user has access to database."""
        with self.session(commit=False) as session:
            access = (
                session.query(UserDatabaseAccessEntity)
                .filter_by(user_id=user_id, db_name=db_name, is_active=True)
                .first()
            )
            return access is not None

    def grant_database_access(
        self, user_id: int, db_name: str, granted_by: int
    ) -> UserDatabaseAccessEntity:
        """Grant database access to user."""
        access = UserDatabaseAccessEntity(
            user_id=user_id, db_name=db_name, granted_by=granted_by
        )
        return self.create(access)

    def revoke_database_access(self, user_id: int, db_name: str) -> bool:
        """Revoke database access from user."""
        with self.session() as session:
            access = (
                session.query(UserDatabaseAccessEntity)
                .filter_by(user_id=user_id, db_name=db_name)
                .first()
            )
            if access:
                access.is_active = False
                session.merge(access)
                return True
            return False


class SessionDao(BaseDao[SessionEntity, Dict[str, Any], Dict[str, Any]]):
    """Session DAO."""

    def get_by_session_id(self, session_id: str) -> Optional[SessionEntity]:
        """Get session by session ID."""
        with self.session(commit=False) as session:
            return (
                session.query(SessionEntity)
                .filter_by(session_id=session_id, is_active=True)
                .first()
            )

    def get_active_user_sessions(self, user_id: int) -> List[SessionEntity]:
        """Get all active sessions for user."""
        with self.session(commit=False) as session:
            return (
                session.query(SessionEntity)
                .filter_by(user_id=user_id, is_active=True)
                .filter(SessionEntity.expires_at > datetime.now())
                .all()
            )

    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a session."""
        with self.session() as session:
            session_entity = (
                session.query(SessionEntity)
                .filter_by(session_id=session_id)
                .first()
            )
            if session_entity:
                session_entity.is_active = False
                session.merge(session_entity)
                return True
            return False

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        with self.session() as session:
            count = (
                session.query(SessionEntity)
                .filter(SessionEntity.expires_at <= datetime.now())
                .update({"is_active": False})
            )
            return count 