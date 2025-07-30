"""
Operation class for representing data transformations in the lineage graph.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime


class Operation:
    """
    Represents a data operation/transformation in the lineage graph.

    An operation captures what transformation was applied to convert
    input data nodes into output data nodes.
    """

    def __init__(self,
                 operation_type: str,
                 inputs: List[str],
                 outputs: List[str],
                 metadata: Optional[Dict] = None):
        """
        Initialize an operation.

        Args:
            operation_type: Type of operation (e.g., 'merge', 'filter', 'aggregate')
            inputs: List of input node IDs
            outputs: List of output node IDs
            metadata: Additional metadata about the operation
        """
        self.id = str(uuid.uuid4())
        self.operation_type = operation_type
        self.inputs = inputs
        self.outputs = outputs
        self.created_at = datetime.now()
        self.metadata = metadata or {}

        # Operation details
        self.parameters: Dict[str, Any] = {}
        self.execution_time: Optional[float] = None
        self.status = "completed"  # pending, running, completed, failed

    def add_parameter(self, key: str, value: Any):
        """Add a parameter to this operation."""
        self.parameters[key] = value

    def set_execution_time(self, time_seconds: float):
        """Set the execution time for this operation."""
        self.execution_time = time_seconds

    def set_status(self, status: str):
        """Set the operation status."""
        self.status = status

    def to_dict(self) -> Dict:
        """Convert operation to dictionary representation."""
        return {
            'id': self.id,
            'operation_type': self.operation_type,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'created_at': self.created_at.isoformat(),
            'parameters': self.parameters,
            'execution_time': self.execution_time,
            'status': self.status,
            'metadata': self.metadata
        }

    def __str__(self) -> str:
        return f"Operation(type='{self.operation_type}', inputs={len(self.inputs)}, outputs={len(self.outputs)})"

    def __repr__(self) -> str:
        return self.__str__()


class PandasOperation(Operation):
    """
    Specialized operation for pandas DataFrame transformations.
    """

    def __init__(self,
                 operation_type: str,
                 inputs: List[str],
                 outputs: List[str],
                 method_name: str,
                 args: Optional[tuple] = None,
                 kwargs: Optional[Dict] = None,
                 metadata: Optional[Dict] = None):
        """
        Initialize a pandas operation.

        Args:
            operation_type: Type of operation
            inputs: List of input node IDs
            outputs: List of output node IDs
            method_name: Name of the pandas method called
            args: Positional arguments passed to the method
            kwargs: Keyword arguments passed to the method
            metadata: Additional metadata
        """
        super().__init__(operation_type, inputs, outputs, metadata)
        self.method_name = method_name
        self.args = args or ()
        self.kwargs = kwargs or {}

        # Store method details in parameters
        self.parameters.update({
            'method_name': method_name,
            'args': args,
            'kwargs': kwargs
        })

    def to_dict(self) -> Dict:
        """Convert pandas operation to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'method_name': self.method_name,
            'args': self.args,
            'kwargs': self.kwargs
        })
        return base_dict


class SQLOperation(Operation):
    """
    Specialized operation for SQL-based transformations.
    """

    def __init__(self,
                 operation_type: str,
                 inputs: List[str],
                 outputs: List[str],
                 sql_query: str,
                 database_type: str = "unknown",
                 metadata: Optional[Dict] = None):
        """
        Initialize a SQL operation.

        Args:
            operation_type: Type of operation
            inputs: List of input node IDs
            outputs: List of output node IDs
            sql_query: SQL query that was executed
            database_type: Type of database (postgresql, mysql, sqlite, etc.)
            metadata: Additional metadata
        """
        super().__init__(operation_type, inputs, outputs, metadata)
        self.sql_query = sql_query
        self.database_type = database_type

        # Store SQL details in parameters
        self.parameters.update({
            'sql_query': sql_query,
            'database_type': database_type
        })

    def to_dict(self) -> Dict:
        """Convert SQL operation to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'sql_query': self.sql_query,
            'database_type': self.database_type
        })
        return base_dict


class FileOperation(Operation):
    """
    Specialized operation for file-based transformations.
    """

    def __init__(self,
                 operation_type: str,
                 inputs: List[str],
                 outputs: List[str],
                 file_format: str,
                 file_path: str,
                 metadata: Optional[Dict] = None):
        """
        Initialize a file operation.

        Args:
            operation_type: Type of operation (read, write)
            inputs: List of input node IDs
            outputs: List of output node IDs
            file_format: Format of the file (csv, json, parquet, etc.)
            file_path: Path to the file
            metadata: Additional metadata
        """
        super().__init__(operation_type, inputs, outputs, metadata)
        self.file_format = file_format
        self.file_path = file_path

        # Store file details in parameters
        self.parameters.update({
            'file_format': file_format,
            'file_path': file_path
        })

    def to_dict(self) -> Dict:
        """Convert file operation to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update({
            'file_format': self.file_format,
            'file_path': self.file_path
        })
        return base_dict
