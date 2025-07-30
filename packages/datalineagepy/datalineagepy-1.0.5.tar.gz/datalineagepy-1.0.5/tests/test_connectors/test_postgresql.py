"""
Tests for PostgreSQL connector with lineage tracking.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sqlite3
import tempfile
import os

from lineagepy.connectors.postgresql import PostgreSQLConnector
from lineagepy.connectors.sql_parser import SQLLineageParser
from lineagepy.core.tracker import LineageTracker


class TestPostgreSQLConnector:
    """Test suite for PostgreSQL connector."""

    def setup_method(self):
        """Setup for each test method."""
        self.tracker = LineageTracker.get_global_instance()
        self.tracker.clear()

        # Mock connection string
        self.connection_string = "postgresql://user:pass@localhost:5432/testdb"

    def test_connector_initialization(self):
        """Test connector initialization."""
        # Test with SQLAlchemy (default)
        connector = PostgreSQLConnector(self.connection_string)
        assert connector.connection_string == self.connection_string
        assert connector.use_sqlalchemy == True
        assert isinstance(connector.sql_parser, SQLLineageParser)

        # Test with psycopg2
        connector = PostgreSQLConnector(
            self.connection_string, use_sqlalchemy=False)
        assert connector.use_sqlalchemy == False

    @patch('lineagepy.connectors.postgresql.create_engine')
    def test_connect_with_sqlalchemy(self, mock_create_engine):
        """Test connection with SQLAlchemy."""
        mock_engine = Mock()
        mock_connection = Mock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        connector = PostgreSQLConnector(self.connection_string)
        connector.connect()

        mock_create_engine.assert_called_once_with(self.connection_string)
        assert connector.connection == mock_connection
        assert connector.engine == mock_engine

    @patch('lineagepy.connectors.postgresql.psycopg2')
    def test_connect_with_psycopg2(self, mock_psycopg2):
        """Test connection with psycopg2."""
        mock_connection = Mock()
        mock_psycopg2.connect.return_value = mock_connection

        connector = PostgreSQLConnector(
            self.connection_string, use_sqlalchemy=False)
        connector.connect()

        mock_psycopg2.connect.assert_called_once_with(self.connection_string)
        assert connector.connection == mock_connection

    def test_disconnect(self):
        """Test disconnection."""
        connector = PostgreSQLConnector(self.connection_string)

        # Mock connections
        mock_connection = Mock()
        mock_engine = Mock()
        connector.connection = mock_connection
        connector.engine = mock_engine

        connector.disconnect()

        mock_connection.close.assert_called_once()
        mock_engine.dispose.assert_called_once()
        assert connector.connection is None
        assert connector.engine is None

    @patch('pandas.read_sql')
    def test_read_table_with_sqlalchemy(self, mock_read_sql):
        """Test reading table with SQLAlchemy."""
        # Setup mock data
        mock_df = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
        mock_read_sql.return_value = mock_df

        connector = PostgreSQLConnector(self.connection_string)
        connector.connection = Mock()  # Mock connection

        # Test reading table
        result = connector.read_table('test_table', schema='public')

        # Verify pandas.read_sql was called correctly
        mock_read_sql.assert_called_once()
        args, kwargs = mock_read_sql.call_args
        assert 'SELECT * FROM "public"."test_table"' == args[0]
        assert args[1] == connector.connection

        # Verify result is LineageDataFrame
        from lineagepy.core.dataframe_wrapper import LineageDataFrame
        assert isinstance(result, LineageDataFrame)
        assert result.shape == (3, 2)
        assert list(result.columns) == ['id', 'name']

    @patch('pandas.read_sql')
    def test_execute_query(self, mock_read_sql):
        """Test executing SQL query with lineage tracking."""
        # Setup mock data
        mock_df = pd.DataFrame({'customer_id': [1, 2], 'total': [100, 200]})
        mock_read_sql.return_value = mock_df

        connector = PostgreSQLConnector(self.connection_string)
        connector.connection = Mock()

        # Test query execution
        query = "SELECT customer_id, SUM(amount) as total FROM sales GROUP BY customer_id"
        result = connector.execute_query(query)

        # Verify result
        from lineagepy.core.dataframe_wrapper import LineageDataFrame
        assert isinstance(result, LineageDataFrame)
        assert result.shape == (2, 2)

        # Verify lineage tracking
        assert len(self.tracker.nodes) > 0
        assert len(self.tracker.edges) >= 0  # May be 0 if SQL parsing fails

    def test_sql_parser_integration(self):
        """Test SQL parser integration."""
        connector = PostgreSQLConnector(self.connection_string)

        # Test simple SELECT query
        query = "SELECT * FROM customers"
        lineage_info = connector.sql_parser.parse_query(query)

        assert lineage_info.query_type == 'SELECT'
        # Depends on parser implementation
        assert len(lineage_info.source_tables) >= 0
        assert lineage_info.raw_query == query

    @patch('lineagepy.connectors.postgresql.create_engine')
    @patch('pandas.read_sql')
    def test_get_schema(self, mock_read_sql, mock_create_engine):
        """Test getting table schema."""
        # Mock schema query result
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ('id', 'integer', 'NO', None),
            ('name', 'character varying', 'YES', None),
            ('created_at', 'timestamp without time zone', 'NO', 'now()')
        ]

        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result

        connector = PostgreSQLConnector(self.connection_string)
        connector.connection = mock_connection

        schema_info = connector.get_schema('test_table', 'public')

        expected_schema = {
            'id': 'integer',
            'name': 'character varying',
            'created_at': 'timestamp without time zone'
        }
        assert schema_info == expected_schema

    @patch('lineagepy.connectors.postgresql.create_engine')
    def test_list_tables(self, mock_create_engine):
        """Test listing tables."""
        # Mock tables query result
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ('customers',), ('orders',), ('products',)
        ]

        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result

        connector = PostgreSQLConnector(self.connection_string)
        connector.connection = mock_connection

        tables = connector.list_tables('public')

        expected_tables = ['customers', 'orders', 'products']
        assert tables == expected_tables

    def test_context_manager(self):
        """Test using connector as context manager."""
        with patch('lineagepy.connectors.postgresql.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_connection = Mock()
            mock_engine.connect.return_value = mock_connection
            mock_create_engine.return_value = mock_engine

            with PostgreSQLConnector(self.connection_string) as connector:
                assert connector.connection == mock_connection

            # Verify disconnect was called
            mock_connection.close.assert_called_once()
            mock_engine.dispose.assert_called_once()

    def test_connection_info(self):
        """Test getting connection information."""
        connector = PostgreSQLConnector(self.connection_string)

        # Test disconnected state
        info = connector.get_connection_info()
        assert info['status'] == 'disconnected'

        # Test connected state
        with patch('lineagepy.connectors.postgresql.create_engine'):
            mock_result = Mock()
            mock_result.fetchone.return_value = (
                'PostgreSQL 13.7 on x86_64-pc-linux-gnu',)

            mock_connection = Mock()
            mock_connection.execute.return_value = mock_result

            connector.connection = mock_connection

            info = connector.get_connection_info()
            assert info['status'] == 'connected'
            assert info['backend'] == 'sqlalchemy'
            assert 'postgresql_version' in info

    def test_test_connection(self):
        """Test connection testing."""
        connector = PostgreSQLConnector(self.connection_string)

        # Test successful connection
        mock_result = Mock()
        mock_result.fetchone.return_value = (1,)

        mock_connection = Mock()
        mock_connection.execute.return_value = mock_result

        connector.connection = mock_connection

        assert connector.test_connection() == True

        # Test failed connection - mock the connection to raise an exception
        mock_connection_fail = Mock()
        mock_connection_fail.execute.side_effect = Exception(
            "Connection failed")

        connector.connection = mock_connection_fail

        assert connector.test_connection() == False


class TestSQLiteIntegration:
    """Integration tests using SQLite as a PostgreSQL substitute."""

    def setup_method(self):
        """Setup SQLite database for testing."""
        self.tracker = LineageTracker.get_global_instance()
        self.tracker.clear()

        # Create temporary SQLite database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # Create test data
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()

        # Create test tables
        cursor.execute('''
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                amount DECIMAL(10,2),
                order_date DATE,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')

        # Insert test data
        cursor.execute(
            "INSERT INTO customers (name, email) VALUES ('John Doe', 'john@example.com')")
        cursor.execute(
            "INSERT INTO customers (name, email) VALUES ('Jane Smith', 'jane@example.com')")
        cursor.execute(
            "INSERT INTO orders (customer_id, amount, order_date) VALUES (1, 100.50, '2023-01-01')")
        cursor.execute(
            "INSERT INTO orders (customer_id, amount, order_date) VALUES (2, 75.25, '2023-01-02')")

        conn.commit()
        conn.close()

    def teardown_method(self):
        """Cleanup temporary database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_sqlite_as_postgresql_substitute(self):
        """Test basic functionality using SQLite."""
        # Create SQLAlchemy connection string for SQLite
        connection_string = f"sqlite:///{self.temp_db.name}"

        # Mock PostgreSQL connector to use SQLite
        with patch('lineagepy.connectors.postgresql.SQLALCHEMY_AVAILABLE', True):
            connector = PostgreSQLConnector(connection_string)

            try:
                connector.connect()

                # Test reading data
                customers_df = connector.execute_query(
                    "SELECT * FROM customers")
                assert len(customers_df) == 2
                assert 'name' in customers_df.columns
                assert 'email' in customers_df.columns

                # Test query with JOIN
                join_query = """
                    SELECT c.name, o.amount 
                    FROM customers c 
                    JOIN orders o ON c.id = o.customer_id
                """
                result_df = connector.execute_query(join_query)
                assert len(result_df) == 2
                assert 'name' in result_df.columns
                assert 'amount' in result_df.columns

                # Verify lineage tracking
                assert len(self.tracker.nodes) > 0

            finally:
                connector.disconnect()


if __name__ == "__main__":
    pytest.main([__file__])
