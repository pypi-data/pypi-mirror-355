"""
SQL lineage parser for extracting data lineage from SQL queries.
"""

import re
import logging
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import sqlparse
    from sqlparse.sql import Statement, IdentifierList, Identifier, Function
    from sqlparse.tokens import Keyword, DML
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False
    logger.warning("sqlparse not available. SQL parsing will be limited.")


@dataclass
class TableReference:
    """Represents a table reference in SQL."""
    name: str
    alias: Optional[str] = None
    schema: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get the full table name including schema."""
        if self.schema:
            return f"{self.schema}.{self.name}"
        return self.name


@dataclass
class ColumnReference:
    """Represents a column reference in SQL."""
    name: str
    table: Optional[str] = None
    alias: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get the full column name including table."""
        if self.table:
            return f"{self.table}.{self.name}"
        return self.name


@dataclass
class SQLLineageInfo:
    """Contains lineage information extracted from SQL."""
    source_tables: List[TableReference]
    target_tables: List[TableReference]
    column_mappings: Dict[str, List[str]]  # target_column -> [source_columns]
    operations: List[str]
    query_type: str
    raw_query: str


class SQLLineageParser:
    """
    Parse SQL queries to extract data lineage information.

    Supports common SQL operations including SELECT, INSERT, UPDATE, DELETE,
    CREATE TABLE AS SELECT (CTAS), and more.
    """

    def __init__(self):
        """Initialize the SQL parser."""
        self.supported_operations = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE',
            'CREATE', 'DROP', 'ALTER', 'WITH'
        }

    def parse_query(self, sql: str) -> SQLLineageInfo:
        """
        Parse SQL query and extract lineage information.

        Args:
            sql: SQL query string

        Returns:
            SQLLineageInfo containing extracted lineage
        """
        if not SQLPARSE_AVAILABLE:
            return self._parse_with_regex(sql)

        try:
            # Parse SQL using sqlparse
            parsed = sqlparse.parse(sql)
            if not parsed:
                return self._create_empty_lineage(sql)

            statement = parsed[0]
            query_type = self._get_query_type(statement)

            if query_type == 'SELECT':
                return self._parse_select(statement, sql)
            elif query_type == 'INSERT':
                return self._parse_insert(statement, sql)
            elif query_type == 'UPDATE':
                return self._parse_update(statement, sql)
            elif query_type == 'DELETE':
                return self._parse_delete(statement, sql)
            elif query_type == 'CREATE':
                return self._parse_create(statement, sql)
            else:
                return self._parse_generic(statement, sql, query_type)

        except Exception as e:
            logger.error(f"Error parsing SQL with sqlparse: {str(e)}")
            return self._parse_with_regex(sql)

    def _get_query_type(self, statement: Statement) -> str:
        """Extract the query type from parsed statement."""
        for token in statement.tokens:
            if token.ttype is DML or token.ttype is Keyword:
                return token.value.upper()
        return 'UNKNOWN'

    def _parse_select(self, statement: Statement, sql: str) -> SQLLineageInfo:
        """Parse SELECT statement."""
        source_tables = []
        column_mappings = {}
        operations = ['SELECT']

        # Extract FROM clause tables
        from_tables = self._extract_from_tables(statement)
        source_tables.extend(from_tables)

        # Extract JOIN tables
        join_tables = self._extract_join_tables(statement)
        source_tables.extend(join_tables)

        # Extract column mappings from SELECT clause
        select_columns = self._extract_select_columns(statement)
        for col_alias, source_cols in select_columns.items():
            column_mappings[col_alias] = source_cols

        return SQLLineageInfo(
            source_tables=source_tables,
            target_tables=[],  # SELECT doesn't create tables
            column_mappings=column_mappings,
            operations=operations,
            query_type='SELECT',
            raw_query=sql
        )

    def _parse_insert(self, statement: Statement, sql: str) -> SQLLineageInfo:
        """Parse INSERT statement."""
        source_tables = []
        target_tables = []
        column_mappings = {}
        operations = ['INSERT']

        # Extract target table
        target_table = self._extract_insert_target(statement)
        if target_table:
            target_tables.append(target_table)

        # Check if it's INSERT ... SELECT
        if 'SELECT' in sql.upper():
            operations.append('SELECT')
            # Extract source tables from SELECT part
            select_part = self._extract_select_from_insert(statement)
            if select_part:
                select_lineage = self._parse_select(select_part, sql)
                source_tables.extend(select_lineage.source_tables)
                column_mappings.update(select_lineage.column_mappings)

        return SQLLineageInfo(
            source_tables=source_tables,
            target_tables=target_tables,
            column_mappings=column_mappings,
            operations=operations,
            query_type='INSERT',
            raw_query=sql
        )

    def _parse_update(self, statement: Statement, sql: str) -> SQLLineageInfo:
        """Parse UPDATE statement."""
        source_tables = []
        target_tables = []
        operations = ['UPDATE']

        # Extract target table (table being updated)
        target_table = self._extract_update_target(statement)
        if target_table:
            target_tables.append(target_table)
            # Target table is also a source for UPDATE
            source_tables.append(target_table)

        # Extract JOIN tables if any
        join_tables = self._extract_join_tables(statement)
        source_tables.extend(join_tables)

        return SQLLineageInfo(
            source_tables=source_tables,
            target_tables=target_tables,
            column_mappings={},  # Complex to extract from UPDATE SET
            operations=operations,
            query_type='UPDATE',
            raw_query=sql
        )

    def _parse_delete(self, statement: Statement, sql: str) -> SQLLineageInfo:
        """Parse DELETE statement."""
        source_tables = []
        target_tables = []
        operations = ['DELETE']

        # Extract target table
        target_table = self._extract_delete_target(statement)
        if target_table:
            target_tables.append(target_table)
            # Target table is also a source for DELETE
            source_tables.append(target_table)

        return SQLLineageInfo(
            source_tables=source_tables,
            target_tables=target_tables,
            column_mappings={},
            operations=operations,
            query_type='DELETE',
            raw_query=sql
        )

    def _parse_create(self, statement: Statement, sql: str) -> SQLLineageInfo:
        """Parse CREATE statement (especially CREATE TABLE AS SELECT)."""
        source_tables = []
        target_tables = []
        operations = ['CREATE']

        # Extract target table name
        target_table = self._extract_create_target(statement)
        if target_table:
            target_tables.append(target_table)

        # Check if it's CREATE TABLE AS SELECT (CTAS)
        if 'SELECT' in sql.upper():
            operations.append('SELECT')
            # Extract source tables from SELECT part
            select_part = self._extract_select_from_create(statement)
            if select_part:
                select_lineage = self._parse_select(select_part, sql)
                source_tables.extend(select_lineage.source_tables)

        return SQLLineageInfo(
            source_tables=source_tables,
            target_tables=target_tables,
            column_mappings={},
            operations=operations,
            query_type='CREATE',
            raw_query=sql
        )

    def _parse_generic(self, statement: Statement, sql: str, query_type: str) -> SQLLineageInfo:
        """Parse generic SQL statement."""
        return SQLLineageInfo(
            source_tables=[],
            target_tables=[],
            column_mappings={},
            operations=[query_type],
            query_type=query_type,
            raw_query=sql
        )

    def _extract_from_tables(self, statement: Statement) -> List[TableReference]:
        """Extract tables from FROM clause."""
        tables = []
        # This is a simplified implementation
        # In practice, you'd need more sophisticated parsing
        from_seen = False

        for token in statement.flatten():
            if token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True
                continue

            if from_seen and token.ttype is None and not token.is_whitespace:
                # Simple table name extraction
                table_name = token.value.strip()
                if table_name and not table_name.upper() in {'WHERE', 'GROUP', 'ORDER', 'HAVING', 'JOIN'}:
                    tables.append(TableReference(name=table_name))
                    break

        return tables

    def _extract_join_tables(self, statement: Statement) -> List[TableReference]:
        """Extract tables from JOIN clauses."""
        tables = []
        # Simplified JOIN extraction
        tokens = list(statement.flatten())

        for i, token in enumerate(tokens):
            if token.ttype is Keyword and 'JOIN' in token.value.upper():
                # Look for table name after JOIN
                for j in range(i + 1, len(tokens)):
                    next_token = tokens[j]
                    if next_token.ttype is None and not next_token.is_whitespace:
                        table_name = next_token.value.strip()
                        if table_name:
                            tables.append(TableReference(name=table_name))
                        break

        return tables

    def _extract_select_columns(self, statement: Statement) -> Dict[str, List[str]]:
        """Extract column mappings from SELECT clause."""
        # Simplified column extraction
        # In practice, this would need much more sophisticated parsing
        return {}

    def _extract_insert_target(self, statement: Statement) -> Optional[TableReference]:
        """Extract target table from INSERT statement."""
        # Simplified implementation
        tokens = list(statement.flatten())
        insert_seen = False

        for token in tokens:
            if token.ttype is DML and token.value.upper() == 'INSERT':
                insert_seen = True
                continue

            if insert_seen and token.ttype is Keyword and token.value.upper() == 'INTO':
                continue

            if insert_seen and token.ttype is None and not token.is_whitespace:
                table_name = token.value.strip()
                if table_name:
                    return TableReference(name=table_name)

        return None

    def _extract_update_target(self, statement: Statement) -> Optional[TableReference]:
        """Extract target table from UPDATE statement."""
        tokens = list(statement.flatten())
        update_seen = False

        for token in tokens:
            if token.ttype is DML and token.value.upper() == 'UPDATE':
                update_seen = True
                continue

            if update_seen and token.ttype is None and not token.is_whitespace:
                table_name = token.value.strip()
                if table_name:
                    return TableReference(name=table_name)

        return None

    def _extract_delete_target(self, statement: Statement) -> Optional[TableReference]:
        """Extract target table from DELETE statement."""
        tokens = list(statement.flatten())
        from_seen = False

        for token in tokens:
            if token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True
                continue

            if from_seen and token.ttype is None and not token.is_whitespace:
                table_name = token.value.strip()
                if table_name:
                    return TableReference(name=table_name)

        return None

    def _extract_create_target(self, statement: Statement) -> Optional[TableReference]:
        """Extract target table from CREATE statement."""
        tokens = list(statement.flatten())
        table_seen = False

        for token in tokens:
            if token.ttype is Keyword and token.value.upper() == 'TABLE':
                table_seen = True
                continue

            if table_seen and token.ttype is None and not token.is_whitespace:
                table_name = token.value.strip()
                if table_name:
                    return TableReference(name=table_name)

        return None

    def _extract_select_from_insert(self, statement: Statement) -> Optional[Statement]:
        """Extract SELECT part from INSERT ... SELECT statement."""
        # Simplified implementation
        return None

    def _extract_select_from_create(self, statement: Statement) -> Optional[Statement]:
        """Extract SELECT part from CREATE TABLE AS SELECT statement."""
        # Simplified implementation
        return None

    def _parse_with_regex(self, sql: str) -> SQLLineageInfo:
        """
        Fallback parsing using regex when sqlparse is not available.

        This is a basic implementation that handles simple cases.
        """
        sql_upper = sql.upper()

        # Determine query type
        query_type = 'UNKNOWN'
        for op in self.supported_operations:
            if sql_upper.strip().startswith(op):
                query_type = op
                break

        source_tables = []
        target_tables = []
        operations = [query_type] if query_type != 'UNKNOWN' else []

        # Extract table names using regex
        if query_type == 'SELECT':
            # Extract FROM tables
            from_match = re.search(r'FROM\s+(\w+)', sql_upper)
            if from_match:
                source_tables.append(TableReference(name=from_match.group(1)))

            # Extract JOIN tables
            join_matches = re.findall(r'JOIN\s+(\w+)', sql_upper)
            for table in join_matches:
                source_tables.append(TableReference(name=table))

        elif query_type == 'INSERT':
            # Extract target table
            insert_match = re.search(r'INSERT\s+INTO\s+(\w+)', sql_upper)
            if insert_match:
                target_tables.append(TableReference(
                    name=insert_match.group(1)))

            # Check for INSERT ... SELECT
            if 'SELECT' in sql_upper:
                operations.append('SELECT')
                from_match = re.search(r'FROM\s+(\w+)', sql_upper)
                if from_match:
                    source_tables.append(
                        TableReference(name=from_match.group(1)))

        return SQLLineageInfo(
            source_tables=source_tables,
            target_tables=target_tables,
            column_mappings={},
            operations=operations,
            query_type=query_type,
            raw_query=sql
        )

    def _create_empty_lineage(self, sql: str) -> SQLLineageInfo:
        """Create empty lineage info for unparseable queries."""
        return SQLLineageInfo(
            source_tables=[],
            target_tables=[],
            column_mappings={},
            operations=[],
            query_type='UNKNOWN',
            raw_query=sql
        )
