"""Serve module for authentication service."""

import logging
from typing import List, Optional, Union

from sqlalchemy import URL

from dbgpt.component import SystemApp
from dbgpt.storage.metadata import DatabaseManager
from dbgpt_serve.core import BaseServe

from .api.endpoints import init_endpoints, router
from .config import (
    APP_NAME,
    SERVE_APP_NAME,
    SERVE_CONFIG_KEY_PREFIX,
    ServeConfig,
)

logger = logging.getLogger(__name__)


class Serve(BaseServe):
    """Serve component for authentication."""

    name = SERVE_APP_NAME

    def __init__(
        self,
        system_app: SystemApp,
        config: Optional[ServeConfig] = None,
        api_prefix: Optional[str] = None,
        api_tags: Optional[List[str]] = None,
        db_url_or_db: Union[str, URL, DatabaseManager] = None,
        try_create_tables: Optional[bool] = False,
    ):
        if not api_prefix:
            api_prefix = f"/api/v1/auth"
        if not api_tags:
            api_tags = ["Authentication"]
            
        super().__init__(
            system_app, api_prefix, api_tags, db_url_or_db, try_create_tables
        )
        self._config = config

    def init_app(self, system_app: SystemApp):
        if self._app_has_initiated:
            return
        self._system_app = system_app
        
        # Include router with prefix
        if isinstance(self._api_prefix, list):
            for prefix in self._api_prefix:
                self._system_app.app.include_router(
                    router, prefix=prefix, tags=self._api_tags
                )
        else:
            self._system_app.app.include_router(
                router, prefix=self._api_prefix, tags=self._api_tags
            )
        
        # Get or create config
        self._config = self._config or ServeConfig.from_app_config(
            system_app.config, SERVE_CONFIG_KEY_PREFIX
        )
        
        # Initialize endpoints
        init_endpoints(self._system_app, self._config)
        self._app_has_initiated = True

    def on_init(self):
        """Called when the serve is initialized."""
        pass 