"""
Comprehensive testing framework for DataLineagePy.

This module provides:
- Advanced assertion utilities
- Performance testing tools
- Quality assurance validators
- Test data generators
- Benchmarking utilities
- Edge case validators
"""

from .assertions import (
    assert_column_lineage,
    assert_table_lineage,
    assert_transformation_count,
    assert_node_exists,
    assert_edge_exists,
    assert_dag_validity,
    assert_lineage_quality,
    assert_performance_metrics
)

from .validators import (
    LineageValidator,
    QualityValidator,
    PerformanceValidator,
    SchemaValidator
)

from .generators import (
    TestDataGenerator,
    LineageTestCase,
    PerformanceTestSuite
)

from .benchmarks import (
    LineageBenchmark,
    PerformanceBenchmark,
    ScalabilityTest
)

from .fixtures import (
    sample_dataframes,
    complex_pipeline,
    large_dataset,
    edge_case_data
)

__all__ = [
    # Assertions
    'assert_column_lineage',
    'assert_table_lineage',
    'assert_transformation_count',
    'assert_node_exists',
    'assert_edge_exists',
    'assert_dag_validity',
    'assert_lineage_quality',
    'assert_performance_metrics',

    # Validators
    'LineageValidator',
    'QualityValidator',
    'PerformanceValidator',
    'SchemaValidator',

    # Generators
    'TestDataGenerator',
    'LineageTestCase',
    'PerformanceTestSuite',

    # Benchmarks
    'LineageBenchmark',
    'PerformanceBenchmark',
    'ScalabilityTest',

    # Fixtures
    'sample_dataframes',
    'complex_pipeline',
    'large_dataset',
    'edge_case_data',
]
