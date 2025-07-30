"""
DataLineagePy Phase 2: File Format Support Demo

This example demonstrates the new file format connectors introduced in Phase 2:
- Parquet Connector (with Apache Arrow integration)
- CSV Connector (with automatic encoding/delimiter detection) 
- JSON/JSONL Connector (with nested data normalization)
"""

import pandas as pd
import json
import tempfile
from pathlib import Path

from lineagepy.connectors.parquet import ParquetConnector
from lineagepy.connectors.csv import CSVConnector
from lineagepy.connectors.json import JSONConnector
from lineagepy.core.tracker import LineageTracker


def main():
    """Demonstrate Phase 2 file format capabilities."""

    print("🚀 DataLineagePy Phase 2: File Format Support Demo")
    print("=" * 60)

    # Initialize shared lineage tracker
    tracker = LineageTracker()

    # Create sample dataset
    sample_data = pd.DataFrame({
        'employee_id': [1, 2, 3, 4, 5],
        'name': ['Alice Johnson', 'Bob Smith', 'Charlie Brown', 'Diana Prince', 'Eve Wilson'],
        'department': ['Engineering', 'Marketing', 'Sales', 'Engineering', 'HR'],
        'salary': [95000, 70000, 65000, 105000, 75000],
        'hire_date': ['2021-01-15', '2020-03-22', '2022-07-10', '2019-11-05', '2021-09-30'],
        'is_manager': [True, False, False, True, False]
    })

    print(
        f"📊 Sample dataset created: {sample_data.shape[0]} employees, {sample_data.shape[1]} columns")
    print(sample_data.head())
    print()

    # === PARQUET CONNECTOR DEMO ===
    print("1️⃣  PARQUET CONNECTOR DEMO")
    print("-" * 30)

    try:
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as parquet_file:
            parquet_file.close()

            # Save as Parquet
            sample_data.to_parquet(parquet_file.name, engine='pyarrow')
            print(f"✅ Saved data to Parquet: {parquet_file.name}")

            # Read with Parquet connector
            parquet_connector = ParquetConnector(
                parquet_file.name, tracker=tracker)
            parquet_df = parquet_connector.read_file()

            print(
                f"📈 Read Parquet file: {parquet_df.shape[0]} rows, {parquet_df.shape[1]} columns")
            print(f"🔗 Lineage tracked: {len(tracker.nodes)} nodes in graph")

            # Demonstrate columnar reading
            salary_data = parquet_connector.read_file(
                columns=['name', 'salary'])
            print(f"📊 Columnar read (name, salary): {salary_data.shape}")

            # Get schema information
            schema = parquet_connector.get_schema()
            print(f"📋 Schema detected: {list(schema.keys())}")

            # Clean up
            Path(parquet_file.name).unlink()
            print()
    except ImportError:
        print("⚠️  PyArrow not available, skipping Parquet demo")
        print()


if __name__ == "__main__":
    main()
