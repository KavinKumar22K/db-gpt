"""Trino connector."""

import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional, Tuple, Type, cast
from urllib.parse import quote
from urllib.parse import quote_plus as urlquote

from sqlalchemy import text

from dbgpt.core.awel.flow import (
    TAGS_ORDER_HIGH,
    ResourceCategory,
    auto_register_resource,
)
from dbgpt.datasource.rdbms.base import RDBMSConnector, RDBMSDatasourceParameters
from dbgpt.util.i18n_utils import _

logger = logging.getLogger(__name__)


@auto_register_resource(
    label=_("Trino datasource"),
    category=ResourceCategory.DATABASE,
    tags={"order": TAGS_ORDER_HIGH},
    description=_(
        "Distributed SQL query engine for running interactive analytic queries "
        "against data sources of all sizes."
    ),
)
@dataclass
class TrinoParameters(RDBMSDatasourceParameters):
    """Trino connection parameters."""

    __type__ = "trino"
    catalog: str = field(
        default="system",
        metadata={"help": _("Trino catalog name, defaults to 'system'")}
    )
    schema: str = field(
        default="default",
        metadata={"help": _("Trino schema name, defaults to 'default'")}
    )
    driver: str = field(
        default="trino",
        metadata={"help": _("Driver name for Trino, default is 'trino'.")},
    )

    def create_connector(self) -> "TrinoConnector":
        """Create Trino connector."""
        return TrinoConnector.from_parameters(self)

    def db_url(self, ssl: bool = False, charset: Optional[str] = None) -> str:
        """Create database URL for Trino."""
        return (
            f"{self.driver}://{self.user}@{self.host}:{self.port}/"
            f"{self.catalog}/{self.schema}"
        )


class TrinoConnector(RDBMSConnector):
    """Trino connector."""

    driver = "trino"
    db_type = "trino"
    db_dialect = "trino"

    @classmethod
    def param_class(cls) -> Type[TrinoParameters]:
        """Return the parameter class."""
        return TrinoParameters

    @classmethod
    def from_uri_db(
        cls,
        host: str,
        port: int,
        user: str,
        pwd: str,
        db_name: str,
        engine_args: Optional[dict] = None,
        **kwargs: Any,
    ) -> "TrinoConnector":
        """Create a new TrinoConnector from host, port, user, pwd, db_name."""
        catalog = kwargs.get("catalog", "system")
        schema = kwargs.get("schema", "default")
        db_url = f"{cls.driver}://{quote(user)}:{urlquote(pwd)}@{host}:{port}/{catalog}/{schema}"
        return cast(TrinoConnector, cls.from_uri(db_url, engine_args, **kwargs))

    @classmethod
    def from_parameters(cls, parameters: TrinoParameters) -> "RDBMSConnector":
        """Create a new connector from parameters."""
        return cls.from_uri_db(
            parameters.host,
            parameters.port,
            parameters.user,
            parameters.password,
            parameters.database,
            catalog=parameters.catalog,
            schema=parameters.schema,
            engine_args=parameters.engine_args(),
        )

    def _sync_tables_from_db(self) -> Iterable[str]:
        """Read table information from database with schema support."""
        schema = self._schema or "default"
        catalog = getattr(self, "catalog", "system")

        with self.session_scope() as session:
            # Get tables for specific schema and catalog
            cursor = session.execute(
                text(
                    f"SELECT table_name FROM system.metadata.table_comments "
                    f"WHERE catalog_name = '{catalog}' AND schema_name = '{schema}'"
                )
            )
            return [row[0] for row in cursor.fetchall() if row[0] is not None]

    def get_grants_info(self) -> List[str]:
        """Get grants info.

        Returns:
            List[str]: grants info
        """
        return []  # Not supported in Trino

    def get_collation(self) -> Optional[str]:
        """Get collation.

        Returns:
            str: collation
        """
        return None  # Not applicable in Trino

    def get_users(self) -> List[str]:
        """Get user info.

        Returns:
            List[str]: user info
        """
        return []  # Not supported in Trino

    def get_columns(self, table_name: str) -> List[dict]:
        """Get columns.

        Args:
            table_name (str): table name

        Returns:
            List[dict]: columns
        """
        schema = self._schema or "default"
        catalog = getattr(self, "catalog", "system")
        
        with self.session_scope() as session:
            columns = []
            cursor = session.execute(
                text(
                    f"SELECT column_name, data_type, comment "
                    f"FROM system.metadata.table_comments "
                    f"WHERE catalog_name = '{catalog}' "
                    f"AND schema_name = '{schema}' "
                    f"AND table_name = '{table_name}'"
                )
            )
            for row in cursor.fetchall():
                columns.append(
                    {
                        "column_name": row[0],
                        "data_type": row[1],
                        "comment": row[2],
                    }
                )
            return columns

    def get_table_comments(self, table_name: str) -> str:
        """Get table comments.

        Args:
            table_name (str): table name

        Returns:
            str: table comments
        """
        schema = self._schema or "default"
        catalog = getattr(self, "catalog", "system")
        
        with self.session_scope() as session:
            cursor = session.execute(
                text(
                    f"SELECT comment "
                    f"FROM system.metadata.table_comments "
                    f"WHERE catalog_name = '{catalog}' "
                    f"AND schema_name = '{schema}' "
                    f"AND table_name = '{table_name}'"
                )
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] else ""

    def get_indexes(self, table_name: str) -> List[dict]:
        """Get table indexes.

        Args:
            table_name (str): table name

        Returns:
            List[dict]: indexes
        """
        return []  # Indexes are not directly exposed in Trino

    def get_show_create_table(self, table_name: str) -> str:
        """Get show create table.

        Args:
            table_name (str): table name

        Returns:
            str: show create table sql
        """
        return f"SHOW CREATE TABLE {table_name}"

    def get_fields(self, table_name: str) -> List[tuple]:
        """Get fields.

        Args:
            table_name (str): table name

        Returns:
            List[tuple]: fields
        """
        schema = self._schema or "default"
        catalog = getattr(self, "catalog", "system")
        
        with self.session_scope() as session:
            cursor = session.execute(
                text(
                    f"SELECT column_name, data_type "
                    f"FROM system.metadata.table_comments "
                    f"WHERE catalog_name = '{catalog}' "
                    f"AND schema_name = '{schema}' "
                    f"AND table_name = '{table_name}'"
                )
            )
            return [(row[0], row[1]) for row in cursor.fetchall()]

    def get_simple_fields(self, table_name: str) -> List[tuple]:
        """Get simple fields.

        Args:
            table_name (str): table name

        Returns:
            List[tuple]: fields
        """
        return self.get_fields(table_name)
