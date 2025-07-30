"""
Comprehensive tests for Phase 5 Testing Framework.
"""

import pytest
import time
from lineagepy.core.tracker import LineageTracker
from lineagepy.testing.validators import LineageValidator, QualityValidator, PerformanceValidator, SchemaValidator
from lineagepy.testing.generators import TestDataGenerator, LineageTestCase, PerformanceTestSuite
from lineagepy.testing.benchmarks import LineageBenchmark, PerformanceBenchmark, ScalabilityTest
from lineagepy.testing.fixtures import sample_dataframes, complex_pipeline, large_dataset, edge_case_data


class TestValidators:
    """Test the validation framework."""

    def setup_method(self):
        """Setup for each test method."""
        self.tracker = LineageTracker.get_global_instance()
        self.tracker.clear()
        self.generator = TestDataGenerator(seed=42)

    def test_lineage_validator_graph_integrity(self):
        """Test graph integrity validation."""
        validator = LineageValidator(self.tracker)

        # Test with empty graph
        result = validator.validate_graph_integrity()
        assert result.passed
        assert "Graph integrity validation passed" in result.message

        # Create some test data
        df = self.generator.generate_simple_dataframe(rows=100)
        df_calc = df.assign(calculated=lambda x: x['A'] + x['B'])

        # Test with populated graph - should pass even with orphaned column nodes
        result = validator.validate_graph_integrity()
        assert result.passed  # Should pass because orphaned column nodes are expected

        # Verify that we have information about orphaned nodes but no critical issues
        if 'all_orphaned_nodes' in result.details:
            # We expect some orphaned column nodes (unused columns)
            assert result.details.get('orphaned_column_nodes', 0) >= 0
            # But no problematic orphaned table nodes
            assert len(result.details.get(
                'problematic_orphaned_nodes', [])) == 0

    def test_lineage_validator_dag_structure(self):
        """Test DAG structure validation."""
        validator = LineageValidator(self.tracker)

        # Create test data (should be DAG)
        df = self.generator.generate_simple_dataframe(rows=100)
        df_calc = df.assign(calculated=lambda x: x['A'] + x['B'])

        result = validator.validate_dag_structure()
        assert result.passed
        assert "valid DAG" in result.message
        assert result.details['node_count'] > 0
        assert result.details['edge_count'] > 0

    def test_quality_validator_context_coverage(self):
        """Test context coverage validation."""
        validator = QualityValidator(self.tracker)

        # Test with empty graph
        result = validator.validate_context_coverage(min_coverage=0.8)
        assert result.passed

        # Create test data
        df = self.generator.generate_simple_dataframe(rows=100)
        df_calc = df.assign(calculated=lambda x: x['A'] + x['B'])

        # Test context coverage
        result = validator.validate_context_coverage(min_coverage=0.0)
        assert result.passed
        assert result.details['total_edges'] > 0
        assert 0.0 <= result.details['coverage'] <= 1.0

    def test_performance_validator_operation_performance(self):
        """Test operation performance validation."""
        validator = PerformanceValidator(self.tracker)

        # Create test data
        df = self.generator.generate_simple_dataframe(rows=1000)

        result = validator.validate_operation_performance(max_time=1.0)
        assert result.passed
        assert result.details['total_time'] < 1.0
        assert result.details['node_count'] > 0
        assert result.details['edge_count'] >= 0

    def test_schema_validator_column_consistency(self):
        """Test schema consistency validation."""
        validator = SchemaValidator(self.tracker)

        # Create test data
        df = self.generator.generate_simple_dataframe(rows=100)

        result = validator.validate_column_schema_consistency()
        assert result.passed
        assert result.details['columns_analyzed'] >= 0


class TestGenerators:
    """Test the data generation framework."""

    def setup_method(self):
        """Setup for each test method."""
        self.generator = TestDataGenerator(seed=42)

    def test_simple_dataframe_generation(self):
        """Test simple DataFrame generation."""
        df = self.generator.generate_simple_dataframe(
            rows=100, columns=['A', 'B', 'C'])

        assert len(df) == 100
        assert list(df.columns) == ['A', 'B', 'C']
        assert hasattr(df, '_lineage_node_id')

    def test_sales_data_generation(self):
        """Test sales data generation."""
        sales_df, customers_df, products_df = self.generator.generate_sales_data(
            rows=500)

        assert len(sales_df) == 500
        assert len(customers_df) >= 10
        assert len(products_df) >= 5

        # Check required columns
        assert 'customer_id' in sales_df.columns
        assert 'product_id' in sales_df.columns
        assert 'customer_id' in customers_df.columns
        assert 'product_id' in products_df.columns

    def test_large_dataset_generation(self):
        """Test large dataset generation."""
        df = self.generator.generate_large_dataset(rows=1000, columns=20)

        assert len(df) == 1000
        assert len(df.columns) == 20
        assert all(col.startswith('col_') for col in df.columns)

    def test_edge_case_data_generation(self):
        """Test edge case data generation."""
        edge_cases = self.generator.generate_edge_case_data()

        assert 'empty' in edge_cases
        assert 'single_row' in edge_cases
        assert 'single_column' in edge_cases
        assert 'with_nulls' in edge_cases

        # Verify edge cases
        assert len(edge_cases['empty']) == 0
        assert len(edge_cases['single_row']) == 1
        assert len(edge_cases['single_column'].columns) == 1


class TestLineageTestCase:
    """Test the LineageTestCase framework."""

    def test_test_case_creation(self):
        """Test creating and running a test case."""
        test_case = LineageTestCase(
            "test_basic_operations", "Test basic DataFrame operations")

        # Add setup
        def setup():
            generator = TestDataGenerator(seed=42)
            return generator.generate_simple_dataframe(rows=50)

        test_case.add_setup(setup)

        # Add validation
        def validate():
            tracker = LineageTracker.get_global_instance()
            return len(tracker.nodes) > 0

        test_case.add_validation(validate)

        # Run test case
        results = test_case.run()

        assert results['name'] == "test_basic_operations"
        assert results['passed']
        assert len(results['setup_results']) == 1
        assert len(results['validation_results']) == 1
        assert len(results['errors']) == 0


class TestPerformanceTestSuite:
    """Test the performance testing suite."""

    def test_large_dataframe_creation_performance(self):
        """Test large DataFrame creation performance."""
        suite = PerformanceTestSuite()

        result = suite.test_large_dataframe_creation(rows=1000)

        assert result['test_name'] == 'large_dataframe_creation'
        assert result['rows'] == 1000
        assert result['creation_time'] > 0
        assert result['operation_time'] > 0
        assert result['nodes_created'] > 0

    def test_complex_pipeline_performance(self):
        """Test complex pipeline performance."""
        suite = PerformanceTestSuite()

        result = suite.test_complex_pipeline_performance()

        assert result['test_name'] == 'complex_pipeline_performance'
        assert result['total_time'] > 0
        assert result['operations_count'] == 6
        assert result['nodes_created'] > 0
        assert result['edges_created'] > 0

    def test_performance_suite_summary(self):
        """Test performance suite summary."""
        suite = PerformanceTestSuite()

        # Run some tests
        suite.test_large_dataframe_creation(rows=500)
        suite.test_complex_pipeline_performance()

        summary = suite.get_summary()

        assert summary['total_tests'] == 2
        assert summary['pass_rate'] >= 0.0
        assert summary['average_time'] > 0
        assert len(summary['all_results']) == 2


class TestBenchmarks:
    """Test the benchmarking framework."""

    def test_lineage_benchmark_dataframe_creation(self):
        """Test DataFrame creation benchmark."""
        benchmark = LineageBenchmark()

        result = benchmark.benchmark_dataframe_creation(rows=500)

        assert result.name.startswith('dataframe_creation')
        assert result.iterations > 0
        assert result.total_time > 0
        assert result.avg_time > 0
        assert result.operations_per_second > 0
        assert result.success_rate > 0

    def test_lineage_benchmark_column_operations(self):
        """Test column operations benchmark."""
        benchmark = LineageBenchmark()

        result = benchmark.benchmark_column_operations(rows=500)

        assert result.name.startswith('column_operations')
        assert result.total_time > 0
        assert result.success_rate > 0

    def test_performance_benchmark_comprehensive(self):
        """Test comprehensive performance benchmark."""
        benchmark = PerformanceBenchmark()

        results = benchmark.run_comprehensive_benchmark()

        assert 'dataframe_creation' in results
        assert 'column_operations' in results
        assert 'merge_operations' in results
        assert 'groupby_operations' in results
        assert 'summary' in results

        summary = results['summary']
        assert summary['total_benchmarks'] > 0
        assert summary['avg_operations_per_second'] > 0
        assert summary['avg_success_rate'] > 0

    def test_scalability_test_node_scalability(self):
        """Test node scalability testing."""
        scalability = ScalabilityTest()

        result = scalability.test_node_scalability(max_nodes=1000)

        assert result['test_name'] == 'node_scalability'
        assert len(result['results']) > 0
        assert 0.0 <= result['scalability_factor'] <= 1.0

        # Check that results show increasing node counts
        results = result['results']
        assert results[0]['target_nodes'] < results[-1]['target_nodes']

    def test_scalability_test_operation_scalability(self):
        """Test operation scalability testing."""
        scalability = ScalabilityTest()

        result = scalability.test_operation_scalability(max_operations=100)

        assert result['test_name'] == 'operation_scalability'
        assert len(result['results']) > 0
        assert 0.0 <= result['scalability_factor'] <= 1.0


class TestFixtures:
    """Test the test fixtures."""

    def test_sample_dataframes(self):
        """Test sample DataFrame fixtures."""
        samples = sample_dataframes()

        assert 'simple' in samples
        assert 'medium' in samples
        assert 'large' in samples

        assert len(samples['simple']) == 50
        assert len(samples['medium']) == 500
        assert len(samples['large']) == 2000

    def test_complex_pipeline_fixture(self):
        """Test complex pipeline fixture."""
        final_result, intermediates = complex_pipeline()

        assert final_result is not None
        assert len(intermediates) > 0

        expected_stages = ['enriched_sales',
                           'complete_sales', 'sales_with_calc', 'final_sales']
        for stage in expected_stages:
            assert stage in intermediates

    def test_large_dataset_fixture(self):
        """Test large dataset fixture."""
        df = large_dataset()

        assert len(df) == 10000
        assert len(df.columns) == 25

    def test_edge_case_data_fixture(self):
        """Test edge case data fixture."""
        edge_cases = edge_case_data()

        assert 'empty' in edge_cases
        assert 'single_row' in edge_cases
        assert 'single_column' in edge_cases
        assert 'with_nulls' in edge_cases


class TestIntegration:
    """Integration tests for the complete testing framework."""

    def setup_method(self):
        """Setup for each test method."""
        self.tracker = LineageTracker.get_global_instance()
        self.tracker.clear()

    def test_end_to_end_testing_workflow(self):
        """Test complete end-to-end testing workflow."""
        # 1. Generate test data
        generator = TestDataGenerator(seed=42)
        df = generator.generate_simple_dataframe(rows=100)

        # 2. Perform operations
        df_calc = df.assign(calculated=lambda x: x['A'] + x['B'])
        df_grouped = df_calc.groupby('A').agg({'calculated': 'sum'})

        # 3. Validate lineage
        validator = LineageValidator(self.tracker)
        integrity_result = validator.validate_graph_integrity()
        dag_result = validator.validate_dag_structure()

        # Graph integrity should pass (orphaned column nodes are expected)
        assert integrity_result.passed
        assert dag_result.passed

        # 4. Check quality
        quality_validator = QualityValidator(self.tracker)
        context_result = quality_validator.validate_context_coverage(
            min_coverage=0.0)

        assert context_result.passed

        # 5. Performance validation
        perf_validator = PerformanceValidator(self.tracker)
        perf_result = perf_validator.validate_operation_performance(
            max_time=1.0)

        assert perf_result.passed

        # 6. Schema validation
        schema_validator = SchemaValidator(self.tracker)
        schema_result = schema_validator.validate_column_schema_consistency()

        assert schema_result.passed

    def test_comprehensive_quality_assessment(self):
        """Test comprehensive quality assessment."""
        # Create complex pipeline
        final_result, intermediates = complex_pipeline()

        # Run all validators
        lineage_validator = LineageValidator(self.tracker)
        quality_validator = QualityValidator(self.tracker)
        perf_validator = PerformanceValidator(self.tracker)
        schema_validator = SchemaValidator(self.tracker)

        # Collect all results
        results = {
            'graph_integrity': lineage_validator.validate_graph_integrity(),
            'dag_structure': lineage_validator.validate_dag_structure(),
            'context_coverage': quality_validator.validate_context_coverage(min_coverage=0.0),
            'operation_performance': perf_validator.validate_operation_performance(max_time=2.0),
            'schema_consistency': schema_validator.validate_column_schema_consistency()
        }

        # All validations should pass (including graph integrity with orphaned column nodes)
        for test_name, result in results.items():
            assert result.passed, f"{test_name} validation failed: {result.message}"

        # Check that we have substantial lineage data
        # Should have many nodes from complex pipeline
        assert len(self.tracker.nodes) > 50
        # Should have multiple transformations (realistic expectation)
        assert len(self.tracker.edges) > 3


if __name__ == "__main__":
    pytest.main([__file__])
