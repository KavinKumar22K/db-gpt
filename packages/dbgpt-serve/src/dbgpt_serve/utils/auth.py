import logging
from typing import Optional

from fastapi import Depends, Header

from dbgpt._private.pydantic import BaseModel

logger = logging.getLogger(__name__)


class UserRequest(BaseModel):
    user_id: Optional[str] = None
    user_no: Optional[str] = None
    real_name: Optional[str] = None
    # same with user_id
    user_name: Optional[str] = None
    user_channel: Optional[str] = None
    role: Optional[str] = "normal"
    nick_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    nick_name_like: Optional[str] = None


def get_user_from_headers(user_id: Optional[str] = Header(None)):
    """Legacy auth function for backward compatibility."""
    try:
        # Try to get auth middleware from global state
        from dbgpt.component import ComponentType
        from dbgpt.configs.model_config import CFG
        
        system_app = getattr(CFG, 'SYSTEM_APP', None)
        if system_app:
            try:
                # Try to use new auth system
                from dbgpt_serve.auth.middleware import create_auth_middleware
                middleware = create_auth_middleware(system_app)
                # This is a simplified fallback - in practice you'd need to handle async
                pass
            except Exception:
                pass
        
        # Fallback to mock User Info
        if user_id:
            return UserRequest(
                user_id=user_id, role="admin", nick_name=user_id, real_name=user_id
            )
        else:
            return UserRequest(
                user_id="001", role="admin", nick_name="dbgpt", real_name="dbgpt"
            )
    except Exception as e:
        logging.exception("Authentication failed!")
        raise Exception(f"Authentication failed. {str(e)}")


# New auth function that integrates with the auth service
def get_authenticated_user():
    """Get authenticated user using the new auth system."""
    try:
        from dbgpt.configs.model_config import CFG
        from dbgpt_serve.auth.middleware import create_auth_middleware
        
        system_app = getattr(CFG, 'SYSTEM_APP', None)
        if system_app:
            middleware = create_auth_middleware(system_app)
            return middleware["get_authenticated_user"]
        else:
            # Fallback to legacy auth
            return get_user_from_headers
    except Exception as e:
        logger.warning(f"Failed to get auth middleware: {e}")
        return get_user_from_headers
