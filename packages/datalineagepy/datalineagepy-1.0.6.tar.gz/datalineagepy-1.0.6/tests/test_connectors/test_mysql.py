"""
Comprehensive tests for MySQL connector.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from lineagepy.connectors.mysql import MySQLConnector


class TestMySQLConnector:
    """Test suite for MySQL connector functionality."""

    @pytest.fixture
    def mock_connection_string(self):
        return "mysql://testuser:testpass@localhost:3306/testdb"

    @pytest.fixture
    def sample_dataframe(self):
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35]
        })

    def test_connector_initialization_with_sqlalchemy(self, mock_connection_string):
        """Test MySQL connector initialization with SQLAlchemy."""
        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', True):
            connector = MySQLConnector(
                mock_connection_string, use_sqlalchemy=True)

            assert connector.connection_string == mock_connection_string
            assert connector.use_sqlalchemy == True
            assert connector.connection is None

    def test_connector_initialization_no_dependencies(self, mock_connection_string):
        """Test MySQL connector fails without dependencies."""
        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', False):
            with patch('lineagepy.connectors.mysql.PYMYSQL_AVAILABLE', False):
                with pytest.raises(ImportError):
                    MySQLConnector(mock_connection_string)

    @patch('lineagepy.connectors.mysql.create_engine')
    def test_sqlalchemy_connection(self, mock_create_engine, mock_connection_string):
        """Test SQLAlchemy connection establishment."""
        mock_engine = Mock()
        mock_connection = Mock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', True):
            connector = MySQLConnector(mock_connection_string)
            connector.connect()

            assert connector.engine == mock_engine
            assert connector.connection == mock_connection

    def test_connection_parsing(self, mock_connection_string):
        """Test connection string parsing for PyMySQL."""
        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', False):
            with patch('lineagepy.connectors.mysql.PYMYSQL_AVAILABLE', True):
                connector = MySQLConnector(mock_connection_string)
                params = connector._parse_connection_string()

                expected = {
                    'host': 'localhost',
                    'port': 3306,
                    'user': 'testuser',
                    'password': 'testpass',
                    'database': 'testdb',
                    'charset': 'utf8mb4',
                    'autocommit': True
                }
                assert params == expected

    @patch('lineagepy.connectors.mysql.pd.read_sql')
    def test_read_table_sqlalchemy(self, mock_read_sql, mock_connection_string, sample_dataframe):
        """Test reading table with SQLAlchemy."""
        mock_read_sql.return_value = sample_dataframe

        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', True):
            connector = MySQLConnector(mock_connection_string)
            connector.connection = Mock()

            with patch.object(connector, '_create_lineage_dataframe') as mock_create_lineage:
                mock_lineage_df = Mock()
                mock_create_lineage.return_value = mock_lineage_df

                result = connector.read_table('users')

                assert result == mock_lineage_df
                mock_read_sql.assert_called_once_with(
                    'SELECT * FROM `users`',
                    connector.connection
                )

    def test_get_schema_sqlalchemy(self, mock_connection_string):
        """Test getting table schema with SQLAlchemy."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ('id', 'int', 'NO', None),
            ('name', 'varchar', 'YES', None)
        ]

        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', True):
            connector = MySQLConnector(mock_connection_string)
            connector.connection = Mock()
            connector.connection.execute.return_value = mock_result

            schema = connector.get_schema('users')

            expected = {'id': 'int', 'name': 'varchar'}
            assert schema == expected

    def test_list_tables_sqlalchemy(self, mock_connection_string):
        """Test listing tables with SQLAlchemy."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [('users',), ('orders',)]

        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', True):
            connector = MySQLConnector(mock_connection_string)
            connector.connection = Mock()
            connector.connection.execute.return_value = mock_result

            tables = connector.list_tables()

            expected = ['users', 'orders']
            assert tables == expected

    def test_test_connection_success(self, mock_connection_string):
        """Test successful connection test."""
        mock_result = Mock()
        mock_result.fetchone.return_value = [1]

        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', True):
            connector = MySQLConnector(mock_connection_string)
            connector.connection = Mock()
            connector.connection.execute.return_value = mock_result

            assert connector.test_connection() == True

    def test_test_connection_failure(self, mock_connection_string):
        """Test failed connection test."""
        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', True):
            connector = MySQLConnector(mock_connection_string)
            connector.connection = Mock()
            connector.connection.execute.side_effect = Exception(
                "Connection failed")

            assert connector.test_connection() == False

    def test_disconnect_sqlalchemy(self, mock_connection_string):
        """Test disconnection with SQLAlchemy."""
        with patch('lineagepy.connectors.mysql.SQLALCHEMY_AVAILABLE', True):
            connector = MySQLConnector(mock_connection_string)
            mock_connection = Mock()
            mock_engine = Mock()
            connector.connection = mock_connection
            connector.engine = mock_engine

            connector.disconnect()

            mock_connection.close.assert_called_once()
            mock_engine.dispose.assert_called_once()
            assert connector.connection is None
            assert connector.engine is None
