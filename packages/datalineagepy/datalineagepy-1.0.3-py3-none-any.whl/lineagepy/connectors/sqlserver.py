"""
SQL Server database connector with lineage tracking.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd

from .base import BaseConnector
from .sql_parser import SQLLineageParser
from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    logger.warning(
        "PyODBC not available. SQL Server connector will be disabled.")

try:
    from sqlalchemy import create_engine
    from sqlalchemy.engine import Engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning(
        "SQLAlchemy not available. Some SQL Server features will be limited.")


class SQLServerConnector(BaseConnector):
    """
    SQL Server database connector with automatic lineage tracking.

    Supports both PyODBC and SQLAlchemy backends for maximum flexibility.
    """

    def __init__(self, connection_string: str, use_sqlalchemy: bool = True, **kwargs):
        """
        Initialize SQL Server connector.

        Args:
            connection_string: SQL Server connection string
            use_sqlalchemy: Whether to use SQLAlchemy (recommended) or PyODBC
            **kwargs: Additional connection options
        """
        if not PYODBC_AVAILABLE and not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "Either PyODBC or SQLAlchemy is required for SQL Server connector")

        super().__init__(connection_string, **kwargs)
        self.use_sqlalchemy = use_sqlalchemy and SQLALCHEMY_AVAILABLE
        self.sql_parser = SQLLineageParser()
        self.engine: Optional[Engine] = None

    def connect(self) -> None:
        """Establish SQL Server connection."""
        try:
            if self.use_sqlalchemy:
                # SQLAlchemy connection with SQL Server specific options
                connect_args = {
                    'timeout': 30,
                    'autocommit': True,
                    **self.options
                }

                # Add driver if not specified
                if 'driver' not in self.connection_string.lower():
                    # Try to use the most compatible driver
                    drivers = [
                        'ODBC Driver 18 for SQL Server',
                        'ODBC Driver 17 for SQL Server',
                        'SQL Server Native Client 11.0',
                        'SQL Server'
                    ]

                    available_drivers = pyodbc.drivers() if PYODBC_AVAILABLE else []
                    driver = None
                    for d in drivers:
                        if d in available_drivers:
                            driver = d
                            break

                    if driver:
                        if '?' in self.connection_string:
                            self.connection_string += f'&driver={driver}'
                        else:
                            self.connection_string += f'?driver={driver}'

                self.engine = create_engine(
                    self.connection_string,
                    connect_args=connect_args,
                    fast_executemany=True  # Performance optimization
                )
                self.connection = self.engine.connect()
                logger.info("Connected to SQL Server using SQLAlchemy")
            else:
                # Direct PyODBC connection
                connection_params = self._parse_connection_string()
                self.connection = pyodbc.connect(
                    **connection_params, **self.options)
                logger.info("Connected to SQL Server using PyODBC")

        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Close SQL Server connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None

            if self.engine:
                self.engine.dispose()
                self.engine = None

            logger.info("Disconnected from SQL Server")

        except Exception as e:
            logger.error(f"Error disconnecting from SQL Server: {str(e)}")

    def read_table(self, table_name: str, schema: Optional[str] = None,
                   **kwargs) -> LineageDataFrame:
        """
        Read SQL Server table with lineage tracking.

        Args:
            table_name: Name of the table to read
            schema: Optional schema name (default: dbo)
            **kwargs: Additional pandas.read_sql options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Build table reference (SQL Server uses square brackets)
            if schema:
                full_table_name = f"[{schema}].[{table_name}]"
            else:
                full_table_name = f"[dbo].[{table_name}]"

            query = f"SELECT * FROM {full_table_name}"

            # Read data using pandas
            if self.use_sqlalchemy:
                df = pd.read_sql(query, self.connection, **kwargs)
            else:
                df = pd.read_sql_query(query, self.connection, **kwargs)

            # Create LineageDataFrame with database source tracking
            lineage_df = self._create_lineage_dataframe(df, table_name, schema)

            logger.info(
                f"Read table {full_table_name}: {df.shape[0]} rows, {df.shape[1]} columns")
            return lineage_df

        except Exception as e:
            logger.error(f"Failed to read table {table_name}: {str(e)}")
            raise

    def execute_query(self, query: str, **kwargs) -> LineageDataFrame:
        """
        Execute SQL Server query with lineage tracking.

        Args:
            query: SQL query to execute
            **kwargs: Additional pandas.read_sql options

        Returns:
            LineageDataFrame with query results and lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Parse query for lineage information
            lineage_info = self.sql_parser.parse_query(query)

            # Execute query
            if self.use_sqlalchemy:
                df = pd.read_sql(query, self.connection, **kwargs)
            else:
                df = pd.read_sql_query(query, self.connection, **kwargs)

            # Create LineageDataFrame
            query_name = f"sqlserver_query_{hash(query) % 10000}"
            lineage_df = self._create_lineage_dataframe(df, query_name)

            # Track SQL lineage
            self._track_sql_lineage(lineage_info, lineage_df)

            logger.info(
                f"Executed query: {df.shape[0]} rows, {df.shape[1]} columns")
            return lineage_df

        except Exception as e:
            logger.error(f"Failed to execute query: {str(e)}")
            raise

    def get_schema(self, table_name: str, schema: Optional[str] = None) -> Dict[str, str]:
        """
        Get SQL Server table schema information.

        Args:
            table_name: Name of the table
            schema: Optional schema name (default: dbo)

        Returns:
            Dictionary mapping column names to data types
        """
        if not self.connection:
            self.connect()

        try:
            # Use INFORMATION_SCHEMA for SQL Server
            schema_name = schema or 'dbo'
            query = """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ?
                ORDER BY ORDINAL_POSITION
            """
            params = (table_name, schema_name)

            if self.use_sqlalchemy:
                result = self.connection.execute(query, params)
                columns = result.fetchall()
            else:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                columns = cursor.fetchall()
                cursor.close()

            schema_info = {}
            for col in columns:
                if hasattr(col, '_mapping'):  # SQLAlchemy result
                    col_name = col[0]
                    data_type = col[1]
                else:
                    # PyODBC result
                    col_name = col[0]
                    data_type = col[1]

                schema_info[col_name] = data_type

            return schema_info

        except Exception as e:
            logger.error(
                f"Failed to get schema for table {table_name}: {str(e)}")
            return {}

    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in SQL Server database or schema.

        Args:
            schema: Optional schema name (default: dbo)

        Returns:
            List of table names
        """
        if not self.connection:
            self.connect()

        try:
            if schema:
                query = """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """
                params = (schema,)
            else:
                query = """
                    SELECT TABLE_SCHEMA + '.' + TABLE_NAME as FULL_NAME
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """
                params = ()

            if self.use_sqlalchemy:
                result = self.connection.execute(query, params)
                tables = [row[0] for row in result.fetchall()]
            else:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()

            return tables

        except Exception as e:
            logger.error(f"Failed to list tables in schema {schema}: {str(e)}")
            return []

    def _write_dataframe(self, df: pd.DataFrame, table_name: str,
                         schema: Optional[str], if_exists: str, **kwargs) -> None:
        """Write DataFrame to SQL Server table."""
        if not self.connection:
            self.connect()

        try:
            # Use pandas to_sql for writing
            if self.use_sqlalchemy:
                df.to_sql(
                    table_name,
                    self.connection,
                    schema=schema or 'dbo',
                    if_exists=if_exists,
                    index=False,
                    method='multi',  # Performance optimization
                    **kwargs
                )
            else:
                # For PyODBC, we need to create an engine temporarily
                temp_engine = create_engine(self.connection_string)
                df.to_sql(
                    table_name,
                    temp_engine,
                    schema=schema or 'dbo',
                    if_exists=if_exists,
                    index=False,
                    method='multi',
                    **kwargs
                )
                temp_engine.dispose()

            logger.info(f"Wrote {len(df)} rows to table {table_name}")

        except Exception as e:
            logger.error(
                f"Failed to write DataFrame to table {table_name}: {str(e)}")
            raise

    def _track_sql_lineage(self, lineage_info, result_df: LineageDataFrame) -> None:
        """Track lineage information from SQL parsing."""
        try:
            # Create nodes for source tables
            for table_ref in lineage_info.source_tables:
                table_node_id = f"sqlserver_table_{table_ref.full_name}"

                # Check if node already exists
                if table_node_id not in self.tracker.nodes:
                    from ..core.nodes import TableNode

                    # Get schema for the table
                    schema_info = self.get_schema(
                        table_ref.name, table_ref.schema)

                    table_node = TableNode(
                        id=table_node_id,
                        name=table_ref.full_name,
                        columns=set(schema_info.keys()),
                        source_type="sqlserver",
                        source_location=f"{self.connection_string}/{table_ref.full_name}"
                    )

                    self.tracker.add_node(table_node)

            # Create lineage edge if we have source tables
            if lineage_info.source_tables:
                from ..core.edges import LineageEdge, TransformationType

                source_node_ids = [
                    f"sqlserver_table_{table.full_name}" for table in lineage_info.source_tables]

                edge = LineageEdge(
                    source_node_ids=source_node_ids,
                    target_node_id=result_df._lineage_node_id,
                    transformation_type=TransformationType.CUSTOM,
                    operation_name=f"sqlserver_{lineage_info.query_type.lower()}",
                    parameters={
                        'query': lineage_info.raw_query,
                        'query_type': lineage_info.query_type,
                        'operations': lineage_info.operations
                    },
                    input_columns=set(),  # Would need more sophisticated parsing
                    output_columns=set(result_df.columns)
                )

                self.tracker.add_edge(edge)

        except Exception as e:
            logger.error(f"Failed to track SQL lineage: {str(e)}")

    def _parse_connection_string(self) -> Dict[str, Any]:
        """Parse SQL Server connection string for PyODBC."""
        # Parse connection string format: mssql+pyodbc://user:pass@server/database?driver=...
        import urllib.parse

        parsed = urllib.parse.urlparse(self.connection_string)
        query_params = urllib.parse.parse_qs(parsed.query)

        # Build PyODBC connection string
        driver = query_params.get('driver', ['SQL Server'])[0]

        conn_str_parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={parsed.hostname}",
        ]

        if parsed.port:
            conn_str_parts.append(f"PORT={parsed.port}")

        if parsed.path and parsed.path != '/':
            database = parsed.path.lstrip('/')
            conn_str_parts.append(f"DATABASE={database}")

        if parsed.username:
            conn_str_parts.append(f"UID={parsed.username}")

        if parsed.password:
            conn_str_parts.append(f"PWD={parsed.password}")

        # Add additional parameters
        for key, values in query_params.items():
            if key.lower() not in ['driver']:
                conn_str_parts.append(f"{key.upper()}={values[0]}")

        connection_string = ';'.join(conn_str_parts)

        return {'connection_string': connection_string}

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information and statistics."""
        if not self.connection:
            return {'status': 'disconnected'}

        try:
            info = {
                'status': 'connected',
                'backend': 'sqlalchemy' if self.use_sqlalchemy else 'pyodbc',
                # Hide credentials
                'connection_string': self.connection_string.split('@')[-1],
            }

            # Get SQL Server version
            if self.use_sqlalchemy:
                result = self.connection.execute("SELECT @@VERSION")
                version = result.fetchone()[0]
            else:
                cursor = self.connection.cursor()
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                cursor.close()

            # Extract version number
            import re
            version_match = re.search(
                r'Microsoft SQL Server (\d+\.\d+)', version)
            if version_match:
                info['sqlserver_version'] = version_match.group(1)
            else:
                info['sqlserver_version'] = 'Unknown'

            # Get database name
            if self.use_sqlalchemy:
                result = self.connection.execute("SELECT DB_NAME()")
                database = result.fetchone()[0]
            else:
                cursor = self.connection.cursor()
                cursor.execute("SELECT DB_NAME()")
                database = cursor.fetchone()[0]
                cursor.close()

            info['database'] = database

            return info

        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def test_connection(self) -> bool:
        """Test the SQL Server connection."""
        try:
            if not self.connection:
                self.connect()

            # Simple test query
            if self.use_sqlalchemy:
                result = self.connection.execute("SELECT 1")
                result.fetchone()
            else:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()

            return True

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
