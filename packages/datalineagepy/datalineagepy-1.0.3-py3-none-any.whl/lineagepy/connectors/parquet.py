"""
Parquet file connector with lineage tracking and Apache Arrow integration.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from pathlib import Path

from .file_base import FileConnector
from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    logger.warning(
        "PyArrow not available. Parquet connector will use pandas fallback.")

try:
    import fastparquet
    FASTPARQUET_AVAILABLE = True
except ImportError:
    FASTPARQUET_AVAILABLE = False
    logger.warning(
        "FastParquet not available. Using PyArrow or pandas for Parquet files.")


class ParquetConnector(FileConnector):
    """
    Parquet file connector with automatic lineage tracking.

    Supports both PyArrow and FastParquet backends with schema evolution tracking.
    """

    def __init__(self, file_path: Union[str, Path], use_pyarrow: bool = True, **kwargs):
        """
        Initialize Parquet connector.

        Args:
            file_path: Path to Parquet file or directory
            use_pyarrow: Whether to use PyArrow (recommended) or FastParquet
            **kwargs: Additional connector options
        """
        super().__init__(file_path, **kwargs)
        self.use_pyarrow = use_pyarrow and PYARROW_AVAILABLE
        self.schema_cache = None

        # Validate backend availability
        if not PYARROW_AVAILABLE and not FASTPARQUET_AVAILABLE:
            logger.warning(
                "Neither PyArrow nor FastParquet available. Using pandas fallback.")

    def connect(self) -> None:
        """Validate Parquet file accessibility and format."""
        super().connect()

        try:
            # Validate it's actually a parquet file
            if not self.validate_file_format():
                raise ValueError(
                    f"File is not a valid Parquet file: {self.file_path}")

            logger.info(f"Connected to Parquet file: {self.file_path}")

        except Exception as e:
            logger.error(f"Failed to connect to Parquet file: {str(e)}")
            raise

    def validate_file_format(self) -> bool:
        """Validate that file is a valid Parquet file."""
        try:
            if self.file_path.is_dir():
                # Check for parquet dataset directory
                parquet_files = list(self.file_path.glob("*.parquet"))
                return len(parquet_files) > 0
            else:
                # Check file extension and magic bytes
                if not self.file_path.suffix.lower() == '.parquet':
                    return False

                # Try to read parquet metadata
                if PYARROW_AVAILABLE:
                    pq.read_metadata(str(self.file_path))
                else:
                    pd.read_parquet(str(self.file_path), nrows=1)

                return True

        except Exception as e:
            logger.debug(f"Parquet validation failed: {str(e)}")
            return False

    def read_file(self, columns: Optional[List[str]] = None,
                  filters: Optional[List] = None,
                  **kwargs) -> LineageDataFrame:
        """
        Read Parquet file with lineage tracking.

        Args:
            columns: Specific columns to read (columnar optimization)
            filters: PyArrow filters for predicate pushdown
            **kwargs: Additional pandas.read_parquet options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Prepare read options
            read_kwargs = {
                'columns': columns,
                **kwargs
            }

            # Use PyArrow for better performance and features
            if self.use_pyarrow and PYARROW_AVAILABLE:
                read_kwargs['engine'] = 'pyarrow'
                if filters:
                    read_kwargs['filters'] = filters
            elif FASTPARQUET_AVAILABLE:
                read_kwargs['engine'] = 'fastparquet'

            # Read the parquet file
            df = pd.read_parquet(str(self.file_path), **read_kwargs)

            # Create lineage DataFrame
            operation_name = f"parquet_read"
            if columns:
                operation_name += f"_cols_{len(columns)}"
            if filters:
                operation_name += f"_filtered"

            lineage_df = self._create_file_lineage_dataframe(
                df, operation_name)

            logger.info(
                f"Read Parquet file: {df.shape[0]} rows, {df.shape[1]} columns")
            return lineage_df

        except Exception as e:
            logger.error(f"Failed to read Parquet file: {str(e)}")
            raise

    def get_schema(self) -> Dict[str, str]:
        """
        Get Parquet file schema information with type mapping.

        Returns:
            Dictionary mapping column names to data types
        """
        if self.schema_cache:
            return self.schema_cache

        try:
            if PYARROW_AVAILABLE and self.use_pyarrow:
                # Use PyArrow for precise schema information
                if self.file_path.is_dir():
                    # Dataset schema
                    dataset = pq.ParquetDataset(str(self.file_path))
                    schema = dataset.schema.to_arrow_schema()
                else:
                    # Single file schema
                    parquet_file = pq.ParquetFile(str(self.file_path))
                    schema = parquet_file.schema.to_arrow_schema()

                # Convert Arrow types to pandas-compatible types
                schema_dict = {}
                for i, field in enumerate(schema):
                    arrow_type = field.type
                    pandas_type = self._arrow_to_pandas_type(arrow_type)
                    schema_dict[field.name] = pandas_type

                self.schema_cache = schema_dict
                return schema_dict
            else:
                # Fallback: read small sample and infer types
                sample_df = pd.read_parquet(str(self.file_path), nrows=1)
                schema_dict = {col: str(dtype)
                               for col, dtype in sample_df.dtypes.items()}
                self.schema_cache = schema_dict
                return schema_dict

        except Exception as e:
            logger.error(f"Failed to get Parquet schema: {str(e)}")
            return {}

    def get_sample_data(self, n_rows: int = 5) -> pd.DataFrame:
        """
        Get sample data from Parquet file efficiently.

        Args:
            n_rows: Number of rows to sample

        Returns:
            Sample DataFrame
        """
        try:
            # Use nrows parameter for efficient sampling
            return pd.read_parquet(str(self.file_path), nrows=n_rows)

        except Exception as e:
            logger.error(f"Failed to get sample data: {str(e)}")
            return pd.DataFrame()

    def _arrow_to_pandas_type(self, arrow_type) -> str:
        """Convert Arrow data type to pandas-compatible string."""
        if pa.types.is_integer(arrow_type):
            return 'int64'
        elif pa.types.is_floating(arrow_type):
            return 'float64'
        elif pa.types.is_string(arrow_type) or pa.types.is_binary(arrow_type):
            return 'object'
        elif pa.types.is_temporal(arrow_type):
            return 'datetime64[ns]'
        elif pa.types.is_boolean(arrow_type):
            return 'bool'
        else:
            return 'object'  # Default fallback
