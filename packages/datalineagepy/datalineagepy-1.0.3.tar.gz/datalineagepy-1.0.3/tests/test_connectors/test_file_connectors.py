"""
Tests for file-based connectors (Parquet, CSV, JSON).
"""

import json
import pandas as pd
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from lineagepy.connectors.file_base import FileConnector
from lineagepy.connectors.parquet import ParquetConnector
from lineagepy.connectors.csv import CSVConnector
from lineagepy.connectors.json import JSONConnector
from lineagepy.core.tracker import LineageTracker


class TestParquetConnector:
    """Test ParquetConnector functionality."""

    @pytest.fixture
    def sample_parquet_file(self):
        """Create a sample Parquet file for testing."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
            'age': [25, 30, 35, 28, 42],
        })

        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            try:
                f.close()  # Close file handle before writing
                df.to_parquet(f.name, engine='pyarrow')
                yield f.name
            except ImportError:
                # Skip if pyarrow not available
                pytest.skip("PyArrow not available for testing")

        try:
            Path(f.name).unlink()
        except:
            pass

    def test_parquet_connector_initialization(self, sample_parquet_file):
        """Test ParquetConnector initialization."""
        connector = ParquetConnector(sample_parquet_file)
        assert connector.file_path == Path(sample_parquet_file)

    def test_parquet_read_file(self, sample_parquet_file):
        """Test reading Parquet file with lineage tracking."""
        tracker = LineageTracker()
        connector = ParquetConnector(sample_parquet_file, tracker=tracker)

        # Test basic read
        lineage_df = connector.read_file()
        assert lineage_df.shape[0] == 5
        assert 'name' in lineage_df.columns


class TestCSVConnector:
    """Test CSVConnector functionality."""

    @pytest.fixture
    def sample_csv_file(self):
        """Create a sample CSV file for testing."""
        data = """id,name,age
1,Alice,25
2,Bob,30
3,Charlie,35"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(data)
            f.flush()
            f.close()
            yield f.name

        try:
            Path(f.name).unlink()
        except:
            pass

    def test_csv_connector_initialization(self, sample_csv_file):
        """Test CSVConnector initialization."""
        connector = CSVConnector(sample_csv_file)
        assert connector.file_path == Path(sample_csv_file)

    def test_csv_read_file(self, sample_csv_file):
        """Test reading CSV file with lineage tracking."""
        tracker = LineageTracker()
        connector = CSVConnector(sample_csv_file, tracker=tracker)

        # Test basic read
        lineage_df = connector.read_file()
        assert lineage_df.shape[0] == 3
        assert 'name' in lineage_df.columns


class TestJSONConnector:
    """Test JSONConnector functionality."""

    @pytest.fixture
    def sample_json_file(self):
        """Create a sample JSON file for testing."""
        data = [
            {"id": 1, "name": "Alice", "age": 25},
            {"id": 2, "name": "Bob", "age": 30},
            {"id": 3, "name": "Charlie", "age": 35}
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            f.close()
            yield f.name

        try:
            Path(f.name).unlink()
        except:
            pass

    def test_json_connector_initialization(self, sample_json_file):
        """Test JSONConnector initialization."""
        connector = JSONConnector(sample_json_file)
        assert connector.file_path == Path(sample_json_file)

    def test_json_read_file(self, sample_json_file):
        """Test reading JSON file with lineage tracking."""
        tracker = LineageTracker()
        connector = JSONConnector(sample_json_file, tracker=tracker)

        # Test basic read
        lineage_df = connector.read_file()
        assert lineage_df.shape[0] == 3
        assert 'name' in lineage_df.columns
