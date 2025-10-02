"""Trino connector."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type
import json
from urllib.parse import quote
from urllib.parse import quote_plus as urlquote

from sqlalchemy import text, create_engine

from dbgpt.core.awel.flow import (
    TAGS_ORDER_HIGH,
    ResourceCategory,
    auto_register_resource,
)
from dbgpt.datasource.parameter import BaseDatasourceParameters
from dbgpt.datasource.rdbms.base import RDBMSConnector
from dbgpt.util.i18n_utils import _


@auto_register_resource(
    label=_("Trino datasource"),
    category=ResourceCategory.DATABASE,
    tags={"order": TAGS_ORDER_HIGH},
    description=_(
        "Distributed SQL query engine for big data analytics compatible with ANSI SQL."
    ),
)
@dataclass
class TrinoParameters(BaseDatasourceParameters):
    """Trino connection parameters."""

    __type__ = "trino"

    # Trino uses catalog and schema rather than a single database concept
    # Non-default fields must come first
    host: str = field(metadata={"help": _("Trino coordinator host")})
    user: str = field(metadata={"help": _("Username for Trino")})
    catalog: str = field(metadata={"help": _("Target catalog (e.g., 'postgres', 'tpch')")})

    # Defaulted fields afterwards
    port: int = field(default=8080, metadata={"help": _("Trino coordinator port")})
    schema: str = field(default="public", metadata={"help": _("Target schema (e.g., 'public', 'tiny')")})

    # Optional password for basic auth; many clusters are passwordless
    password: str = field(
        default="",
        metadata={
            "help": _(
                "Password for Trino when using basic authentication (optional)."
            ),
            "tags": "privacy",
        },
    )

    # Optional HTTP scheme (http/https)
    http_scheme: str = field(
        default="http", metadata={"help": _("HTTP scheme: http or https")}
    )

    driver: str = field(
        default="trino",
        metadata={
            "help": _("Driver name for Trino SQLAlchemy dialect, default is 'trino'."),
        },
    )

    # Use JSON string to be UI-friendly; we'll parse it in engine args.
    session_properties: str = field(
        default="",
        metadata={
            "help": _(
                "Session properties as JSON, e.g. {\"query_max_run_time\": \"5m\"}"
            )
        },
    )

    def engine_args(self) -> Optional[Dict[str, Any]]:
        """Build SQLAlchemy engine args for Trino."""
        connect_args: Dict[str, Any] = {}
        # sqlalchemy-trino supports http_scheme and session_properties in connect_args
        if self.http_scheme:
            connect_args["http_scheme"] = self.http_scheme
        if self.session_properties:
            try:
                props = json.loads(self.session_properties)
                if isinstance(props, dict):
                    connect_args["session_properties"] = props
            except Exception:
                # Ignore invalid JSON; user can fix it in UI
                pass
        # Basic authentication can be provided via URL query parameters as well,
        # but we keep connect_args minimal for compatibility
        return {"connect_args": connect_args} if connect_args else None

    def create_connector(self) -> "TrinoConnector":
        return TrinoConnector.from_parameters(self)

    def db_url(self, ssl: bool = False, charset: Optional[str] = None) -> str:
        """Return SQLAlchemy URL for Trino.

        Format: trino://user[:password]@host:port/catalog/schema
        """
        auth = f"{quote(self.user)}"
        if self.password:
            auth = f"{auth}:{urlquote(self.password)}"
        return f"{self.driver}://{auth}@{self.host}:{str(self.port)}/{self.catalog}/{self.schema}"


class TrinoConnector(RDBMSConnector):
    """Trino connector."""

    db_type: str = "trino"
    db_dialect: str = "trino"
    driver: str = "trino"

    @classmethod
    def param_class(cls) -> Type[TrinoParameters]:
        """Return the parameter class."""
        return TrinoParameters

    @classmethod
    def from_parameters(cls, parameters: TrinoParameters) -> "TrinoConnector":
        """Create connector from parameters."""
        db_url = parameters.db_url()
        engine_args = parameters.engine_args() or {}
        return cls(create_engine(db_url, **engine_args))

    @classmethod
    def from_uri_db(
        cls,
        host: str,
        port: int,
        user: str,
        pwd: str,
        catalog: str,
        schema: str = "public",
        engine_args: Optional[dict] = None,
        **kwargs: Any,
    ) -> "TrinoConnector":
        """Create a new TrinoConnector from connection parts."""
        auth = f"{quote(user)}"
        if pwd:
            auth = f"{auth}:{urlquote(pwd)}"
        db_url: str = f"{cls.driver}://{auth}@{host}:{str(port)}/{catalog}/{schema}"
        # Do not forward extraneous kwargs (e.g., db_name) into base __init__
        return cls.from_uri(db_url, engine_args)

    def get_current_db_name(self) -> str:
        """Return current catalog.schema."""
        try:
            with self.session_scope() as session:
                cur = session.execute(text("SELECT current_catalog, current_schema"))
                row = cur.fetchone()
                if row and len(row) == 2:
                    return f"{row[0]}.{row[1]}"
        except Exception:
            pass
        # Fallback to engine URL path
        url = self._engine.url
        # url.database contains 'catalog/schema'
        return url.database or ""

    def _format_sql(self, sql: str) -> str:
        """Format SQL for Trino.

        Trino (sqlalchemy-trino) can raise SYNTAX_ERROR on trailing ';'.
        Strip it here so other datasources remain unaffected.
        """
        if not sql:
            return sql
        sql = sql.strip()
        if sql.endswith(";"):
            sql = sql[:-1].strip()
        return sql

    def table_simple_info(self) -> Iterable[str]:
        """Return simple table info using information_schema."""
        try:
            with self.session_scope() as session:
                # Aggregate column names per table in current schema
                sql = text(
                    """
                    SELECT table_name,
                           array_join(array_agg(column_name), ', ')
                    FROM information_schema.columns
                    WHERE table_schema = current_schema
                    GROUP BY table_name
                    ORDER BY table_name
                    """
                )
                rows = session.execute(sql).fetchall()
                return [f"{r[0]}({r[1]})" for r in rows]
        except Exception:
            return []

    def get_show_create_table(self, table_name: str) -> str:
        """Return SHOW CREATE TABLE result if available."""
        try:
            with self.session_scope() as session:
                cur = session.execute(text(f"SHOW CREATE TABLE {table_name}"))
                rows = cur.fetchall()
                # sqlalchemy-trino returns two columns: Table | Create Table
                if rows:
                    # Pick the second column as the DDL
                    ddl = rows[0][1] if len(rows[0]) > 1 else rows[0][0]
                    return ddl
        except Exception:
            pass
        return ""

    def get_charset(self):
        """Trino is UTF-8 oriented; return UTF-8."""
        return "UTF-8"

    def get_collation(self):
        """Trino does not expose DB-level collation; return UTF-8."""
        return "UTF-8"

    def get_users(self):
        """Not available in Trino via SQL by default."""
        return []

    def get_grants(self):
        """Permissions visibility varies; return empty by default."""
        return []
