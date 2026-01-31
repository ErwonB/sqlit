"""MotherDuck adapter for cloud DuckDB."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlit.domains.connections.providers.duckdb.adapter import DuckDBAdapter

if TYPE_CHECKING:
    from sqlit.domains.connections.domain.config import ConnectionConfig


class MotherDuckAdapter(DuckDBAdapter):
    """Adapter for MotherDuck cloud DuckDB service."""

    @property
    def name(self) -> str:
        return "MotherDuck"

    @property
    def supports_process_worker(self) -> bool:
        """MotherDuck handles concurrency server-side."""
        return True

    def connect(self, config: ConnectionConfig) -> Any:
        """Connect to MotherDuck cloud database."""
        duckdb = self._import_driver_module(
            "duckdb",
            driver_name=self.name,
            extra_name=self.install_extra,
            package_name=self.install_package,
        )

        # Get database from options or tcp_endpoint
        database = config.get_option("database", "")
        if not database and config.tcp_endpoint:
            database = config.tcp_endpoint.database

        # Get token from tcp_endpoint.password (stored in keyring)
        token = ""
        if config.tcp_endpoint:
            token = config.tcp_endpoint.password or ""

        if not database:
            raise ValueError("MotherDuck connections require a database name.")
        if not token:
            raise ValueError("MotherDuck connections require an access token.")

        conn_str = f"md:{database}?motherduck_token={token}"

        duckdb_any: Any = duckdb
        return duckdb_any.connect(conn_str)

    def build_select_query(
        self, table: str, limit: int, database: str | None = None, schema: str | None = None
    ) -> str:
        """Build SELECT LIMIT query for MotherDuck.

        MotherDuck requires three-part names: database.schema.table
        """
        schema = schema or "main"
        if database:
            return f'SELECT * FROM "{database}"."{schema}"."{table}" LIMIT {limit}'
        return f'SELECT * FROM "{schema}"."{table}" LIMIT {limit}'
