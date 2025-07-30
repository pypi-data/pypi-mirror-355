"""
Test data generators for comprehensive lineage testing.
"""

import random
import string
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd

from ..core.dataframe_wrapper import LineageDataFrame
from ..core.tracker import LineageTracker


@dataclass
class TestDataSpec:
    """Specification for generating test data."""
    rows: int = 100
    columns: List[str] = None
    data_types: Dict[str, str] = None
    null_probability: float = 0.1

    def __post_init__(self):
        if self.columns is None:
            self.columns = [f'col_{i}' for i in range(5)]
        if self.data_types is None:
            self.data_types = {col: 'int' for col in self.columns}


class TestDataGenerator:
    """
    Generator for creating test datasets with various characteristics.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the test data generator.

        Args:
            seed: Random seed for reproducible data generation
        """
        if seed is not None:
            random.seed(seed)

    def generate_simple_dataframe(self,
                                  name: str = "test_data",
                                  rows: int = 100,
                                  columns: List[str] = None) -> LineageDataFrame:
        """
        Generate a simple test DataFrame.

        Args:
            name: Name for the DataFrame
            rows: Number of rows to generate
            columns: List of column names

        Returns:
            LineageDataFrame with test data
        """
        if columns is None:
            columns = ['A', 'B', 'C', 'D']

        data = {}
        for col in columns:
            if col.endswith('_id'):
                # Generate ID columns
                data[col] = list(range(1, rows + 1))
            elif col.endswith('_name'):
                # Generate name columns
                data[col] = [f"Name_{i}" for i in range(rows)]
            elif col.endswith('_amount') or col.endswith('_price'):
                # Generate monetary columns
                data[col] = [round(random.uniform(10, 1000), 2)
                             for _ in range(rows)]
            elif col.endswith('_date'):
                # Generate date columns
                data[col] = [
                    f"2023-01-{(i % 28) + 1:02d}" for i in range(rows)]
            else:
                # Generate numeric columns
                data[col] = [random.randint(1, 100) for _ in range(rows)]

        return LineageDataFrame(data, name=name, source_type="generated")

    def generate_sales_data(self, rows: int = 1000) -> Tuple[LineageDataFrame, LineageDataFrame, LineageDataFrame]:
        """
        Generate realistic sales data with multiple related tables.

        Args:
            rows: Number of sales records to generate

        Returns:
            Tuple of (sales, customers, products) DataFrames
        """
        # Generate customers
        customer_count = max(10, rows // 10)
        customers_data = {
            'customer_id': list(range(1, customer_count + 1)),
            'customer_name': [f"Customer_{i}" for i in range(1, customer_count + 1)],
            'tier': [random.choice(['Bronze', 'Silver', 'Gold']) for _ in range(customer_count)],
            'region': [random.choice(['North', 'South', 'East', 'West']) for _ in range(customer_count)]
        }
        customers_df = LineageDataFrame(
            customers_data, name="customers", source_type="database")

        # Generate products
        product_count = max(5, rows // 20)
        products_data = {
            'product_id': [f"P{i:03d}" for i in range(1, product_count + 1)],
            'product_name': [f"Product_{i}" for i in range(1, product_count + 1)],
            'category': [random.choice(['Electronics', 'Clothing', 'Books', 'Home']) for _ in range(product_count)],
            'unit_price': [round(random.uniform(5, 500), 2) for _ in range(product_count)]
        }
        products_df = LineageDataFrame(
            products_data, name="products", source_type="database")

        # Generate sales
        sales_data = {
            'sale_id': list(range(1, rows + 1)),
            'customer_id': [random.randint(1, customer_count) for _ in range(rows)],
            'product_id': [f"P{random.randint(1, product_count):03d}" for _ in range(rows)],
            'quantity': [random.randint(1, 10) for _ in range(rows)],
            'sale_date': [f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}" for _ in range(rows)],
            'discount_percent': [random.choice([0, 5, 10, 15, 20]) for _ in range(rows)]
        }
        sales_df = LineageDataFrame(
            sales_data, name="sales", source_type="database")

        return sales_df, customers_df, products_df

    def generate_large_dataset(self, rows: int = 10000, columns: int = 50) -> LineageDataFrame:
        """
        Generate a large dataset for performance testing.

        Args:
            rows: Number of rows to generate
            columns: Number of columns to generate

        Returns:
            LineageDataFrame with large dataset
        """
        data = {}

        for i in range(columns):
            col_name = f"col_{i:03d}"
            if i % 10 == 0:
                # String columns
                data[col_name] = [f"str_{j % 1000}" for j in range(rows)]
            elif i % 10 == 1:
                # Float columns
                data[col_name] = [random.uniform(0, 1000) for _ in range(rows)]
            else:
                # Integer columns
                data[col_name] = [random.randint(0, 1000) for _ in range(rows)]

        return LineageDataFrame(data, name="large_dataset", source_type="generated")

    def generate_edge_case_data(self) -> Dict[str, LineageDataFrame]:
        """
        Generate datasets with edge cases for testing robustness.

        Returns:
            Dictionary of edge case DataFrames
        """
        edge_cases = {}

        # Empty DataFrame
        edge_cases['empty'] = LineageDataFrame({}, name="empty_data")

        # Single row DataFrame
        edge_cases['single_row'] = LineageDataFrame(
            {'A': [1], 'B': [2], 'C': [3]},
            name="single_row"
        )

        # Single column DataFrame
        edge_cases['single_column'] = LineageDataFrame(
            {'only_col': list(range(100))},
            name="single_column"
        )

        # DataFrame with missing values
        data_with_nulls = {
            'A': [1, None, 3, None, 5],
            'B': [None, 2, None, 4, None],
            'C': [1, 2, 3, 4, 5]
        }
        edge_cases['with_nulls'] = LineageDataFrame(
            data_with_nulls, name="with_nulls")

        # DataFrame with duplicate column names (handled by pandas)
        edge_cases['duplicate_values'] = LineageDataFrame(
            {'A': [1, 1, 1, 2, 2], 'B': [1, 1, 2, 2, 3]},
            name="duplicate_values"
        )

        # DataFrame with special characters in column names
        edge_cases['special_chars'] = LineageDataFrame(
            {'col with spaces': [1, 2, 3], 'col-with-dashes': [4,
                                                               5, 6], 'col_with_underscores': [7, 8, 9]},
            name="special_chars"
        )

        return edge_cases


class LineageTestCase:
    """
    Represents a complete test case with expected lineage outcomes.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize a lineage test case.

        Args:
            name: Name of the test case
            description: Description of what the test case validates
        """
        self.name = name
        self.description = description
        self.setup_functions = []
        self.validation_functions = []
        self.cleanup_functions = []

    def add_setup(self, func):
        """Add a setup function to the test case."""
        self.setup_functions.append(func)
        return self

    def add_validation(self, func):
        """Add a validation function to the test case."""
        self.validation_functions.append(func)
        return self

    def add_cleanup(self, func):
        """Add a cleanup function to the test case."""
        self.cleanup_functions.append(func)
        return self

    def run(self) -> Dict[str, Any]:
        """
        Run the complete test case.

        Returns:
            Dictionary with test results
        """
        results = {
            'name': self.name,
            'description': self.description,
            'passed': True,
            'setup_results': [],
            'validation_results': [],
            'cleanup_results': [],
            'errors': []
        }

        try:
            # Run setup
            for setup_func in self.setup_functions:
                try:
                    setup_result = setup_func()
                    results['setup_results'].append(setup_result)
                except Exception as e:
                    results['errors'].append(f"Setup error: {str(e)}")
                    results['passed'] = False

            # Run validations
            for validation_func in self.validation_functions:
                try:
                    validation_result = validation_func()
                    results['validation_results'].append(validation_result)
                    if hasattr(validation_result, 'passed') and not validation_result.passed:
                        results['passed'] = False
                except Exception as e:
                    results['errors'].append(f"Validation error: {str(e)}")
                    results['passed'] = False

            # Run cleanup
            for cleanup_func in self.cleanup_functions:
                try:
                    cleanup_result = cleanup_func()
                    results['cleanup_results'].append(cleanup_result)
                except Exception as e:
                    results['errors'].append(f"Cleanup error: {str(e)}")

        except Exception as e:
            results['errors'].append(f"Test case error: {str(e)}")
            results['passed'] = False

        return results


class PerformanceTestSuite:
    """
    Suite of performance tests for lineage tracking.
    """

    def __init__(self):
        """Initialize the performance test suite."""
        self.test_results = []

    def test_large_dataframe_creation(self, rows: int = 10000) -> Dict[str, Any]:
        """
        Test performance of creating large DataFrames with lineage tracking.

        Args:
            rows: Number of rows to test with

        Returns:
            Performance test results
        """
        import time

        generator = TestDataGenerator()

        start_time = time.time()
        df = generator.generate_large_dataset(rows=rows, columns=10)
        creation_time = time.time() - start_time

        start_time = time.time()
        # Perform some operations - ensure we use numeric columns
        # col_001 and col_002 are guaranteed to be numeric based on our generation logic
        df_calc = df.assign(
            calculated_col=lambda x: x['col_001'] + x['col_002'])
        operation_time = time.time() - start_time

        tracker = LineageTracker.get_global_instance()

        results = {
            'test_name': 'large_dataframe_creation',
            'rows': rows,
            'creation_time': creation_time,
            'operation_time': operation_time,
            'total_time': creation_time + operation_time,
            'nodes_created': len(tracker.nodes),
            'edges_created': len(tracker.edges),
            'memory_efficient': creation_time < 1.0,  # Should be fast
            'operation_efficient': operation_time < 0.5
        }

        self.test_results.append(results)
        return results

    def test_complex_pipeline_performance(self) -> Dict[str, Any]:
        """
        Test performance of complex data pipeline with multiple operations.

        Returns:
            Performance test results
        """
        import time

        generator = TestDataGenerator()

        start_time = time.time()

        # Create test data
        sales_df, customers_df, products_df = generator.generate_sales_data(
            rows=1000)

        # Complex pipeline
        enriched_sales = sales_df.merge(
            customers_df, on='customer_id', how='left')
        complete_sales = enriched_sales.merge(
            products_df, on='product_id', how='left')

        sales_with_calc = complete_sales.assign(
            total_amount=lambda x: x['quantity'] * x['unit_price'],
            discount_amount=lambda x: x['total_amount'] *
            x['discount_percent'] / 100,
            final_amount=lambda x: x['total_amount'] - x['discount_amount']
        )

        summary = sales_with_calc.groupby(['tier', 'category']).agg({
            'final_amount': ['sum', 'mean', 'count'],
            'quantity': 'sum'
        })

        total_time = time.time() - start_time

        tracker = LineageTracker.get_global_instance()

        results = {
            'test_name': 'complex_pipeline_performance',
            'total_time': total_time,
            'operations_count': 6,  # merge, merge, assign, assign, assign, groupby
            'nodes_created': len(tracker.nodes),
            'edges_created': len(tracker.edges),
            'time_per_operation': total_time / 6,
            'efficient': total_time < 2.0  # Should complete in reasonable time
        }

        self.test_results.append(results)
        return results

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all performance test results.

        Returns:
            Summary of performance test results
        """
        if not self.test_results:
            return {'message': 'No performance tests run'}

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results
                           if result.get('efficient', False) or result.get('memory_efficient', False))

        avg_time = sum(result.get('total_time', 0)
                       for result in self.test_results) / total_tests

        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate': passed_tests / total_tests,
            'average_time': avg_time,
            'all_results': self.test_results
        }
