"""
Phase 5 Testing Framework Demo

This demo showcases the comprehensive testing framework capabilities:
- Advanced validation and quality assurance
- Performance testing and benchmarking
- Test data generation and fixtures
- Automated testing workflows
"""

import time
from lineagepy.core.tracker import LineageTracker
from lineagepy.testing.validators import LineageValidator, QualityValidator, PerformanceValidator, SchemaValidator
from lineagepy.testing.generators import TestDataGenerator, LineageTestCase, PerformanceTestSuite
from lineagepy.testing.benchmarks import LineageBenchmark, PerformanceBenchmark, ScalabilityTest
from lineagepy.testing.fixtures import sample_dataframes, complex_pipeline, large_dataset, edge_case_data


def demo_validation_framework():
    """Demonstrate the validation framework capabilities."""
    print("🔍 VALIDATION FRAMEWORK DEMO")
    print("=" * 50)

    # Clear tracker for clean demo
    tracker = LineageTracker.get_global_instance()
    tracker.clear()

    # Create test data
    generator = TestDataGenerator(seed=42)
    df = generator.generate_simple_dataframe(rows=1000)

    # Perform operations to create lineage
    df_calc = df.assign(
        sum_col=lambda x: x['A'] + x['B'],
        product_col=lambda x: x['C'] * x['D'],
        ratio_col=lambda x: x['A'] / (x['B'] + 1)
    )

    df_grouped = df_calc.groupby('A').agg({
        'sum_col': ['mean', 'sum'],
        'product_col': 'max'
    })

    print(
        f"📊 Created lineage with {len(tracker.nodes)} nodes and {len(tracker.edges)} edges")

    # 1. Graph Integrity Validation
    print("\n1️⃣ Graph Integrity Validation")
    validator = LineageValidator(tracker)
    result = validator.validate_graph_integrity()
    print(f"   Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"   Message: {result.message}")
    if result.details:
        print(f"   Details: {result.details}")

    # 2. DAG Structure Validation
    print("\n2️⃣ DAG Structure Validation")
    result = validator.validate_dag_structure()
    print(f"   Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
    print(f"   Message: {result.message}")
    print(
        f"   Nodes: {result.details.get('node_count', 0)}, Edges: {result.details.get('edge_count', 0)}")

    # 3. Quality Validation
    print("\n3️⃣ Quality Validation")
    quality_validator = QualityValidator(tracker)

    context_result = quality_validator.validate_context_coverage(
        min_coverage=0.5)
    print(
        f"   Context Coverage: {'✅ PASSED' if context_result.passed else '❌ FAILED'}")
    print(f"   Coverage: {context_result.details.get('coverage', 0):.2%}")

    # 4. Performance Validation
    print("\n4️⃣ Performance Validation")
    perf_validator = PerformanceValidator(tracker)
    perf_result = perf_validator.validate_operation_performance(max_time=1.0)
    print(
        f"   Performance: {'✅ PASSED' if perf_result.passed else '❌ FAILED'}")
    print(f"   Total Time: {perf_result.details.get('total_time', 0):.3f}s")

    # 5. Schema Validation
    print("\n5️⃣ Schema Validation")
    schema_validator = SchemaValidator(tracker)
    schema_result = schema_validator.validate_column_schema_consistency()
    print(
        f"   Schema Consistency: {'✅ PASSED' if schema_result.passed else '❌ FAILED'}")
    print(
        f"   Columns Analyzed: {schema_result.details.get('columns_analyzed', 0)}")


def demo_test_data_generation():
    """Demonstrate test data generation capabilities."""
    print("\n\n🏭 TEST DATA GENERATION DEMO")
    print("=" * 50)

    generator = TestDataGenerator(seed=42)

    # 1. Simple DataFrame Generation
    print("\n1️⃣ Simple DataFrame Generation")
    simple_df = generator.generate_simple_dataframe(
        rows=100, columns=['X', 'Y', 'Z'])
    print(f"   Generated DataFrame: {simple_df.shape}")
    print(f"   Columns: {list(simple_df.columns)}")
    print(f"   Sample data:\n{simple_df.head(3)}")

    # 2. Sales Data Generation
    print("\n2️⃣ Realistic Sales Data Generation")
    sales_df, customers_df, products_df = generator.generate_sales_data(
        rows=500)
    print(f"   Sales DataFrame: {sales_df.shape}")
    print(f"   Customers DataFrame: {customers_df.shape}")
    print(f"   Products DataFrame: {products_df.shape}")
    print(f"   Sales sample:\n{sales_df.head(3)}")

    # 3. Large Dataset Generation
    print("\n3️⃣ Large Dataset Generation")
    large_df = generator.generate_large_dataset(rows=5000, columns=20)
    print(f"   Large DataFrame: {large_df.shape}")
    print(
        f"   Memory usage: ~{large_df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

    # 4. Edge Case Data Generation
    print("\n4️⃣ Edge Case Data Generation")
    edge_cases = generator.generate_edge_case_data()
    for name, df in edge_cases.items():
        print(f"   {name}: {df.shape}")


def demo_performance_testing():
    """Demonstrate performance testing capabilities."""
    print("\n\n⚡ PERFORMANCE TESTING DEMO")
    print("=" * 50)

    # 1. Performance Test Suite
    print("\n1️⃣ Performance Test Suite")
    suite = PerformanceTestSuite()

    # Test large DataFrame creation
    result = suite.test_large_dataframe_creation(rows=2000)
    print(f"   Large DataFrame Creation:")
    print(f"   - Creation Time: {result['creation_time']:.3f}s")
    print(f"   - Operation Time: {result['operation_time']:.3f}s")
    print(f"   - Nodes Created: {result['nodes_created']}")
    print(
        f"   - Memory Efficient: {'✅' if result['memory_efficient'] else '❌'}")

    # Test complex pipeline
    result = suite.test_complex_pipeline_performance()
    print(f"\n   Complex Pipeline Performance:")
    print(f"   - Total Time: {result['total_time']:.3f}s")
    print(f"   - Operations: {result['operations_count']}")
    print(f"   - Time per Operation: {result['time_per_operation']:.3f}s")
    print(f"   - Efficient: {'✅' if result['efficient'] else '❌'}")

    # Get summary
    summary = suite.get_summary()
    print(f"\n   📊 Performance Summary:")
    print(f"   - Total Tests: {summary['total_tests']}")
    print(f"   - Pass Rate: {summary['pass_rate']:.2%}")
    print(f"   - Average Time: {summary['average_time']:.3f}s")


def demo_benchmarking():
    """Demonstrate benchmarking capabilities."""
    print("\n\n📊 BENCHMARKING DEMO")
    print("=" * 50)

    # 1. Lineage Benchmark
    print("\n1️⃣ Lineage Operations Benchmark")
    benchmark = LineageBenchmark()

    # Benchmark DataFrame creation
    result = benchmark.benchmark_dataframe_creation(rows=1000)
    print(f"   DataFrame Creation (1000 rows):")
    print(f"   - Average Time: {result.avg_time:.4f}s")
    print(f"   - Operations/sec: {result.operations_per_second:.1f}")
    print(f"   - Success Rate: {result.success_rate:.2%}")

    # Benchmark column operations
    result = benchmark.benchmark_column_operations(rows=1000)
    print(f"\n   Column Operations (1000 rows):")
    print(f"   - Average Time: {result.avg_time:.4f}s")
    print(f"   - Operations/sec: {result.operations_per_second:.1f}")
    print(f"   - Success Rate: {result.success_rate:.2%}")

    # 2. Comprehensive Performance Benchmark
    print("\n2️⃣ Comprehensive Performance Benchmark")
    perf_benchmark = PerformanceBenchmark()
    results = perf_benchmark.run_comprehensive_benchmark()

    summary = results['summary']
    print(f"   📈 Benchmark Summary:")
    print(f"   - Total Benchmarks: {summary['total_benchmarks']}")
    print(
        f"   - Avg Operations/sec: {summary['avg_operations_per_second']:.1f}")
    print(f"   - Avg Success Rate: {summary['avg_success_rate']:.2%}")
    print(f"   - Total Time: {summary['total_time']:.3f}s")


def demo_scalability_testing():
    """Demonstrate scalability testing capabilities."""
    print("\n\n📈 SCALABILITY TESTING DEMO")
    print("=" * 50)

    scalability = ScalabilityTest()

    # 1. Node Scalability Test
    print("\n1️⃣ Node Scalability Test")
    result = scalability.test_node_scalability(max_nodes=2000)

    print(f"   Scalability Factor: {result['scalability_factor']:.3f}")
    print(f"   Test Results:")

    # Show first 3 results
    for i, test_result in enumerate(result['results'][:3]):
        print(f"   - {test_result['target_nodes']} nodes: "
              f"{test_result['time_taken']:.3f}s "
              f"({test_result['nodes_per_second']:.1f} nodes/sec)")

    # 2. Operation Scalability Test
    print("\n2️⃣ Operation Scalability Test")
    result = scalability.test_operation_scalability(max_operations=50)

    print(f"   Scalability Factor: {result['scalability_factor']:.3f}")
    print(f"   Test Results:")

    # Show first 3 results
    for i, test_result in enumerate(result['results'][:3]):
        print(f"   - {test_result['operations']} ops: "
              f"{test_result['time_taken']:.3f}s "
              f"({test_result['operations_per_second']:.1f} ops/sec)")


def demo_test_fixtures():
    """Demonstrate test fixtures capabilities."""
    print("\n\n🧪 TEST FIXTURES DEMO")
    print("=" * 50)

    # 1. Sample DataFrames
    print("\n1️⃣ Sample DataFrames")
    samples = sample_dataframes()
    for name, df in samples.items():
        print(f"   {name}: {df.shape}")

    # 2. Complex Pipeline
    print("\n2️⃣ Complex Pipeline Fixture")
    final_result, intermediates = complex_pipeline()
    print(f"   Final Result: {final_result.shape}")
    print(f"   Intermediate Steps: {len(intermediates)}")
    for name, df in intermediates.items():
        print(f"   - {name}: {df.shape}")

    # 3. Large Dataset
    print("\n3️⃣ Large Dataset Fixture")
    large_df = large_dataset()
    print(f"   Large Dataset: {large_df.shape}")

    # 4. Edge Case Data
    print("\n4️⃣ Edge Case Data Fixtures")
    edge_cases = edge_case_data()
    for name, df in edge_cases.items():
        print(f"   {name}: {df.shape}")


def demo_automated_test_case():
    """Demonstrate automated test case framework."""
    print("\n\n🤖 AUTOMATED TEST CASE DEMO")
    print("=" * 50)

    # Create a comprehensive test case
    test_case = LineageTestCase(
        "comprehensive_lineage_test",
        "Test complete lineage tracking workflow with validation"
    )

    # Setup function
    def setup():
        tracker = LineageTracker.get_global_instance()
        tracker.clear()

        generator = TestDataGenerator(seed=42)
        df = generator.generate_simple_dataframe(rows=500)

        # Perform operations
        df_calc = df.assign(calculated=lambda x: x['A'] + x['B'])
        df_grouped = df_calc.groupby('A').agg({'calculated': 'sum'})

        return {'nodes': len(tracker.nodes), 'edges': len(tracker.edges)}

    # Validation functions
    def validate_graph_integrity():
        tracker = LineageTracker.get_global_instance()
        validator = LineageValidator(tracker)
        return validator.validate_graph_integrity()

    def validate_performance():
        tracker = LineageTracker.get_global_instance()
        validator = PerformanceValidator(tracker)
        return validator.validate_operation_performance(max_time=1.0)

    def validate_quality():
        tracker = LineageTracker.get_global_instance()
        validator = QualityValidator(tracker)
        return validator.validate_context_coverage(min_coverage=0.0)

    # Cleanup function
    def cleanup():
        tracker = LineageTracker.get_global_instance()
        node_count = len(tracker.nodes)
        tracker.clear()
        return {'cleaned_nodes': node_count}

    # Add functions to test case
    test_case.add_setup(setup)
    test_case.add_validation(validate_graph_integrity)
    test_case.add_validation(validate_performance)
    test_case.add_validation(validate_quality)
    test_case.add_cleanup(cleanup)

    # Run the test case
    print("\n🚀 Running Automated Test Case...")
    results = test_case.run()

    print(f"   Test Name: {results['name']}")
    print(f"   Description: {results['description']}")
    print(f"   Status: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")
    print(f"   Setup Results: {len(results['setup_results'])} completed")
    print(
        f"   Validation Results: {len(results['validation_results'])} completed")
    print(f"   Cleanup Results: {len(results['cleanup_results'])} completed")

    if results['errors']:
        print(f"   Errors: {results['errors']}")

    # Show validation details
    for i, validation in enumerate(results['validation_results']):
        if hasattr(validation, 'passed'):
            status = '✅ PASSED' if validation.passed else '❌ FAILED'
            print(f"   Validation {i+1}: {status} - {validation.message}")


def main():
    """Run the complete Phase 5 Testing Framework demo."""
    print("🧪 DATALINEAGEPY PHASE 5: TESTING FRAMEWORK DEMO")
    print("=" * 60)
    print("Comprehensive testing, validation, and quality assurance capabilities")
    print("=" * 60)

    start_time = time.time()

    try:
        # Run all demo sections
        demo_validation_framework()
        demo_test_data_generation()
        demo_performance_testing()
        demo_benchmarking()
        demo_scalability_testing()
        demo_test_fixtures()
        demo_automated_test_case()

        # Final summary
        total_time = time.time() - start_time
        tracker = LineageTracker.get_global_instance()

        print("\n\n🎯 PHASE 5 DEMO SUMMARY")
        print("=" * 50)
        print(f"✅ All testing framework components demonstrated successfully!")
        print(f"⏱️  Total Demo Time: {total_time:.2f} seconds")
        print(
            f"📊 Final Lineage State: {len(tracker.nodes)} nodes, {len(tracker.edges)} edges")
        print("\n🚀 Phase 5 Testing Framework is ready for production use!")

        print("\n📋 CAPABILITIES DEMONSTRATED:")
        print("   ✅ Advanced validation framework")
        print("   ✅ Comprehensive test data generation")
        print("   ✅ Performance testing and benchmarking")
        print("   ✅ Scalability testing")
        print("   ✅ Quality assurance validation")
        print("   ✅ Automated test case framework")
        print("   ✅ Test fixtures and edge cases")
        print("   ✅ Schema consistency validation")

    except Exception as e:
        print(f"\n❌ Demo encountered an error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
