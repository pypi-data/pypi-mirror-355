"""
JSON/JSONL file connector with lineage tracking and nested schema support.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from pathlib import Path

from .file_base import FileConnector
from ..core.dataframe_wrapper import LineageDataFrame

logger = logging.getLogger(__name__)


class JSONConnector(FileConnector):
    """
    JSON/JSONL file connector with automatic lineage tracking.

    Supports both regular JSON files and JSON Lines format with nested data handling.
    """

    def __init__(self, file_path: Union[str, Path],
                 lines: bool = None,
                 normalize_nested: bool = True,
                 max_level: int = 3,
                 **kwargs):
        """
        Initialize JSON connector.

        Args:
            file_path: Path to JSON file
            lines: Whether file is JSON Lines format (auto-detected if None)
            normalize_nested: Whether to flatten nested JSON structures
            max_level: Maximum nesting level to normalize
            **kwargs: Additional connector options
        """
        super().__init__(file_path, **kwargs)
        self.lines = lines
        self.normalize_nested = normalize_nested
        self.max_level = max_level
        self.json_metadata = {}
        self.schema_cache = None

    def validate_file_format(self) -> bool:
        """Validate that file is a valid JSON file."""
        try:
            # Check file extension
            valid_extensions = {'.json', '.jsonl', '.ndjson'}
            if self.file_path.suffix.lower() not in valid_extensions:
                logger.debug(
                    f"Unexpected file extension: {self.file_path.suffix}")

            # Try to parse first few lines as JSON
            with open(self.file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line:
                    return False

                # Try parsing as regular JSON first
                try:
                    json.loads(first_line)
                    return True
                except json.JSONDecodeError:
                    return False

        except Exception as e:
            logger.debug(f"JSON validation failed: {str(e)}")
            return False

    def read_file(self, nrows: Optional[int] = None,
                  lines: Optional[bool] = None,
                  **kwargs) -> LineageDataFrame:
        """
        Read JSON file with lineage tracking.

        Args:
            nrows: Number of records to read (for JSONL)
            lines: Override lines format detection
            **kwargs: Additional pandas options

        Returns:
            LineageDataFrame with tracked lineage
        """
        if not self.connection:
            self.connect()

        try:
            # Determine format
            is_lines = lines if lines is not None else self.lines
            if is_lines is None:
                is_lines = self._detect_jsonl_format()

            # Read the JSON file
            if is_lines:
                df = self._read_jsonl(nrows=nrows, **kwargs)
            else:
                df = self._read_json(**kwargs)

            # Apply normalization if requested
            if self.normalize_nested and not df.empty:
                df = self._normalize_nested_data(df)

            # Create lineage DataFrame
            operation_name = "json_read"
            if is_lines:
                operation_name = "jsonl_read"
            if nrows:
                operation_name += f"_rows_{nrows}"

            lineage_df = self._create_file_lineage_dataframe(
                df, operation_name)

            logger.info(
                f"Read JSON file: {df.shape[0]} rows, {df.shape[1]} columns")
            return lineage_df

        except Exception as e:
            logger.error(f"Failed to read JSON file: {str(e)}")
            raise

    def get_schema(self) -> Dict[str, str]:
        """
        Get JSON file schema information with nested structure analysis.

        Returns:
            Dictionary mapping column names to data types
        """
        if self.schema_cache:
            return self.schema_cache

        try:
            # Read sample to infer schema
            sample_df = self.get_sample_data(n_rows=100)

            if sample_df.empty:
                return {}

            # Analyze schema including nested structures
            schema_dict = {}
            for col in sample_df.columns:
                dtype = sample_df[col].dtype

                if dtype == 'object':
                    # Check if column contains nested data
                    sample_values = sample_df[col].dropna().head(10)

                    contains_dict = any(isinstance(val, dict)
                                        for val in sample_values)
                    contains_list = any(isinstance(val, list)
                                        for val in sample_values)

                    if contains_dict:
                        schema_dict[col] = 'nested_object'
                    elif contains_list:
                        schema_dict[col] = 'nested_array'
                    else:
                        schema_dict[col] = 'text'
                else:
                    schema_dict[col] = str(dtype)

            self.schema_cache = schema_dict
            return schema_dict

        except Exception as e:
            logger.error(f"Failed to get JSON schema: {str(e)}")
            return {}

    def get_sample_data(self, n_rows: int = 5) -> pd.DataFrame:
        """
        Get sample data from JSON file efficiently.

        Args:
            n_rows: Number of rows to sample

        Returns:
            Sample DataFrame
        """
        try:
            is_lines = self._detect_jsonl_format()

            if is_lines:
                return self._read_jsonl(nrows=n_rows)
            else:
                df = self._read_json()
                return df.head(n_rows) if not df.empty else df

        except Exception as e:
            logger.error(f"Failed to get sample data: {str(e)}")
            return pd.DataFrame()

    def _read_json(self, **kwargs) -> pd.DataFrame:
        """Read regular JSON file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert to DataFrame
            if isinstance(data, list):
                # Array of objects
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Single object or nested structure
                df = pd.DataFrame([data])
            else:
                # Scalar value
                df = pd.DataFrame({'value': [data]})

            return df

        except Exception as e:
            logger.error(f"Failed to read JSON: {str(e)}")
            return pd.DataFrame()

    def _read_jsonl(self, nrows: Optional[int] = None, **kwargs) -> pd.DataFrame:
        """Read JSON Lines file."""
        try:
            records = []

            with open(self.file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if nrows and i >= nrows:
                        break

                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            records.append(record)
                        except json.JSONDecodeError as e:
                            logger.warning(
                                f"Skipping invalid JSON line {i+1}: {str(e)}")
                            continue

            return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"Failed to read JSONL: {str(e)}")
            return pd.DataFrame()

    def _normalize_nested_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize nested JSON structures in DataFrame."""
        try:
            if df.empty:
                return df

            # Use pandas json_normalize for nested data
            normalized_df = pd.json_normalize(
                df.to_dict('records'), max_level=self.max_level)

            return normalized_df

        except Exception as e:
            logger.debug(f"Normalization failed, returning original: {str(e)}")
            return df

    def _detect_jsonl_format(self) -> bool:
        """Detect if file is JSON Lines format."""
        try:
            # Check file extension first
            if self.file_path.suffix.lower() in {'.jsonl', '.ndjson'}:
                return True

            # Check content structure
            with open(self.file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip()

                if not first_line:
                    return False

                # Try parsing first line as JSON
                try:
                    json.loads(first_line)

                    # If second line also parses as JSON, likely JSONL
                    if second_line:
                        try:
                            json.loads(second_line)
                            return True
                        except json.JSONDecodeError:
                            pass

                    return False  # Single JSON file

                except json.JSONDecodeError:
                    return False

        except Exception as e:
            logger.debug(f"JSONL detection failed: {str(e)}")
            return False
