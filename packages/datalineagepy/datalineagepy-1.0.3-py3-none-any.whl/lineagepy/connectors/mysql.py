"""
MySQL database connector with lineage tracking.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd

from .base import BaseConnector
from .sql_parser import SQLLineageParser
from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    logger.warning("PyMySQL not available. MySQL connector will be disabled.")

try:
    from sqlalchemy import create_engine
    from sqlalchemy.engine import Engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning(
        "SQLAlchemy not available. Some MySQL features will be limited.")


class MySQLConnector(BaseConnector):
    """
    MySQL database connector with automatic lineage tracking.

    Supports both PyMySQL and SQLAlchemy backends for maximum flexibility.
    """

    def __init__(self, connection_string: str, use_sqlalchemy: bool = True, **kwargs):
        """
        Initialize MySQL connector.

        Args:
            connection_string: MySQL connection string
            use_sqlalchemy: Whether to use SQLAlchemy (recommended) or PyMySQL
            **kwargs: Additional connection options
        """
        if not PYMYSQL_AVAILABLE and not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "Either PyMySQL or SQLAlchemy is required for MySQL connector")

        super().__init__(connection_string, **kwargs)
        self.use_sqlalchemy = use_sqlalchemy and SQLALCHEMY_AVAILABLE
        self.sql_parser = SQLLineageParser()
        self.engine: Optional[Engine] = None

    def connect(self) -> None:
        """Establish MySQL connection."""
        try:
            if self.use_sqlalchemy:
                # Add MySQL-specific options
                connect_args = {
                    'charset': 'utf8mb4',
                    'autocommit': True,
                    **self.options
                }
                self.engine = create_engine(
                    self.connection_string,
                    connect_args=connect_args
                )
                self.connection = self.engine.connect()
                logger.info("Connected to MySQL using SQLAlchemy")
            else:
                # Parse connection string for PyMySQL
                connection_params = self._parse_connection_string()
                self.connection = pymysql.connect(
                    **connection_params, **self.options)
                logger.info("Connected to MySQL using PyMySQL")

        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Close MySQL connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None

            if self.engine:
                self.engine.dispose()
                self.engine = None

            logger.info("Disconnected from MySQL")

        except Exception as e:
            logger.error(f"Error disconnecting from MySQL: {str(e)}")

    def read_table(self, table_name: str, schema: Optional[str] = None,
                   **kwargs) -> LineageDataFrame:
        """
        Read MySQL table with lineage tracking.

        Args:
            table_name: Name of the table to read
            schema: Optional schema/database name
            **kwargs: Additional pandas.read_sql options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Build table reference (MySQL uses backticks)
            if schema:
                full_table_name = f"`{schema}`.`{table_name}`"
            else:
                full_table_name = f"`{table_name}`"

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
        Execute MySQL query with lineage tracking.

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
            query_name = f"mysql_query_{hash(query) % 10000}"
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
        Get MySQL table schema information.

        Args:
            table_name: Name of the table
            schema: Optional schema/database name

        Returns:
            Dictionary mapping column names to data types
        """
        if not self.connection:
            self.connect()

        try:
            # Use INFORMATION_SCHEMA for MySQL
            if schema:
                query = """
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = %s AND TABLE_SCHEMA = %s
                    ORDER BY ORDINAL_POSITION
                """
                params = (table_name, schema)
            else:
                query = """
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE()
                    ORDER BY ORDINAL_POSITION
                """
                params = (table_name,)

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
                col_name = col[0] if isinstance(
                    col, (list, tuple)) else col['COLUMN_NAME']
                data_type = col[1] if isinstance(
                    col, (list, tuple)) else col['DATA_TYPE']
                schema_info[col_name] = data_type

            return schema_info

        except Exception as e:
            logger.error(
                f"Failed to get schema for table {table_name}: {str(e)}")
            return {}

    def list_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        List all tables in MySQL database or schema.

        Args:
            schema: Optional schema/database name

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
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """
                params = (schema,)
            else:
                query = """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
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
        """Write DataFrame to MySQL table."""
        if not self.connection:
            self.connect()

        try:
            # Use pandas to_sql for writing
            if self.use_sqlalchemy:
                df.to_sql(
                    table_name,
                    self.connection,
                    schema=schema,
                    if_exists=if_exists,
                    index=False,
                    **kwargs
                )
            else:
                # For PyMySQL, we need to create an engine temporarily
                temp_engine = create_engine(self.connection_string)
                df.to_sql(
                    table_name,
                    temp_engine,
                    schema=schema,
                    if_exists=if_exists,
                    index=False,
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
                table_node_id = f"mysql_table_{table_ref.full_name}"

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
                        source_type="mysql",
                        source_location=f"{self.connection_string}/{table_ref.full_name}"
                    )

                    self.tracker.add_node(table_node)

            # Create lineage edge if we have source tables
            if lineage_info.source_tables:
                from ..core.edges import LineageEdge, TransformationType

                source_node_ids = [
                    f"mysql_table_{table.full_name}" for table in lineage_info.source_tables]

                edge = LineageEdge(
                    source_node_ids=source_node_ids,
                    target_node_id=result_df._lineage_node_id,
                    transformation_type=TransformationType.CUSTOM,
                    operation_name=f"mysql_{lineage_info.query_type.lower()}",
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
        """Parse MySQL connection string for PyMySQL."""
        # Simple parsing for mysql://user:pass@host:port/database
        import urllib.parse

        parsed = urllib.parse.urlparse(self.connection_string)

        params = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 3306,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/') if parsed.path else None,
            'charset': 'utf8mb4',
            'autocommit': True
        }

        # Remove None values
        return {k: v for k, v in params.items() if v is not None}

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information and statistics."""
        if not self.connection:
            return {'status': 'disconnected'}

        try:
            info = {
                'status': 'connected',
                'backend': 'sqlalchemy' if self.use_sqlalchemy else 'pymysql',
                # Hide credentials
                'connection_string': self.connection_string.split('@')[-1],
            }

            # Get MySQL version
            if self.use_sqlalchemy:
                result = self.connection.execute("SELECT VERSION()")
                version = result.fetchone()[0]
            else:
                cursor = self.connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.close()

            info['mysql_version'] = version.split(
                '-')[0]  # Remove additional info

            return info

        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def test_connection(self) -> bool:
        """Test the MySQL connection."""
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
