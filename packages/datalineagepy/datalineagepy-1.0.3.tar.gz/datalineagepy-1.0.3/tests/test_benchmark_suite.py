#!/usr/bin/env python3
"""
⚡ COMPREHENSIVE BENCHMARK SUITE ⚡
Performance Analysis of DataLineagePy

This suite provides detailed performance benchmarks:
- Operation speed benchmarks
- Memory efficiency analysis
- Scalability testing
- Comparative analysis
- Performance regression detection
"""

import time
import pandas as pd
import numpy as np
import psutil
import gc
import os
from typing import Dict, List, Any, Tuple
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from lineagepy import LineageDataFrame, LineageTracker

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Benchmark result data structure."""
    operation: str
    data_size: int
    execution_time_ns: int
    execution_time_ms: float
    memory_delta_mb: float
    operations_per_second: float
    memory_per_row_kb: float
    cpu_usage_percent: float


class PerformanceBenchmarker:
    """High-precision performance benchmarker."""

    def __init__(self):
        """Initialize benchmarker."""
        self.process = psutil.Process(os.getpid())
        self.results: List[BenchmarkResult] = []

    def benchmark_operation(self, operation_name: str, operation_func, data_size: int) -> BenchmarkResult:
        """Benchmark a single operation with high precision."""
        # Prepare for measurement
        gc.collect()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        start_cpu = self.process.cpu_percent()

        # Execute with nanosecond precision
        start_time = time.perf_counter_ns()
        result = operation_func()
        end_time = time.perf_counter_ns()

        # Measure resources
        end_memory = self.process.memory_info().rss / 1024 / 1024
        end_cpu = self.process.cpu_percent()

        # Calculate metrics
        execution_time_ns = end_time - start_time
        execution_time_ms = execution_time_ns / 1_000_000
        memory_delta_mb = end_memory - start_memory
        operations_per_second = 1_000_000_000 / \
            execution_time_ns if execution_time_ns > 0 else 0
        memory_per_row_kb = (memory_delta_mb * 1024) / \
            data_size if data_size > 0 else 0
        cpu_usage_percent = end_cpu - start_cpu

        benchmark_result = BenchmarkResult(
            operation=operation_name,
            data_size=data_size,
            execution_time_ns=execution_time_ns,
            execution_time_ms=execution_time_ms,
            memory_delta_mb=memory_delta_mb,
            operations_per_second=operations_per_second,
            memory_per_row_kb=memory_per_row_kb,
            cpu_usage_percent=cpu_usage_percent
        )

        self.results.append(benchmark_result)
        return benchmark_result


class TestOperationBenchmarks:
    """Benchmark individual operations."""

    def setup_method(self):
        """Setup for benchmark tests."""
        self.benchmarker = PerformanceBenchmarker()

    def test_creation_benchmark(self):
        """Benchmark DataFrame creation performance."""
        logger.info("⚡ Benchmarking DataFrame creation...")

        sizes = [1000, 10000, 100000]

        for size in sizes:
            def create_operation():
                df = pd.DataFrame({
                    'id': range(size),
                    'value': np.random.randn(size),
                    'category': np.random.choice(['A', 'B', 'C'], size)
                })
                return LineageDataFrame(df, table_name=f"creation_{size}")

            result = self.benchmarker.benchmark_operation(
                f"creation_{size}", create_operation, size
            )

            print(f"📊 Creation {size:,} rows: {result.execution_time_ms:.2f}ms, "
                  f"{result.memory_per_row_kb:.3f}KB/row, {result.operations_per_second:.0f} ops/s")

            # Performance assertions
            assert result.execution_time_ms < 5000, f"Creation too slow: {result.execution_time_ms}ms"
            assert result.memory_per_row_kb < 10, f"Memory usage too high: {result.memory_per_row_kb}KB/row"

    def test_filter_benchmark(self):
        """Benchmark filter operation performance."""
        logger.info("⚡ Benchmarking filter operations...")

        sizes = [1000, 10000, 100000]

        for size in sizes:
            # Prepare data
            df = pd.DataFrame({
                'id': range(size),
                'value': np.random.randn(size)
            })
            ldf = LineageDataFrame(df, table_name=f"filter_test_{size}")

            def filter_operation():
                return ldf.filter(ldf['value'] > 0)

            result = self.benchmarker.benchmark_operation(
                f"filter_{size}", filter_operation, size
            )

            print(f"🔍 Filter {size:,} rows: {result.execution_time_ms:.2f}ms, "
                  f"{result.operations_per_second:.0f} ops/s")

            # Performance assertions
            assert result.execution_time_ms < 2000, f"Filter too slow: {result.execution_time_ms}ms"

    def test_assign_benchmark(self):
        """Benchmark assign operation performance."""
        logger.info("⚡ Benchmarking assign operations...")

        sizes = [1000, 10000, 100000]

        for size in sizes:
            df = pd.DataFrame({
                'a': range(size),
                'b': np.random.randn(size)
            })
            ldf = LineageDataFrame(df, table_name=f"assign_test_{size}")

            def assign_operation():
                return ldf.assign(
                    c=ldf['a'] * 2,
                    d=ldf['b'] + ldf['a'],
                    e=ldf['a'] ** 2
                )

            result = self.benchmarker.benchmark_operation(
                f"assign_{size}", assign_operation, size
            )

            print(f"➕ Assign {size:,} rows: {result.execution_time_ms:.2f}ms, "
                  f"{result.operations_per_second:.0f} ops/s")

            assert result.execution_time_ms < 3000, f"Assign too slow: {result.execution_time_ms}ms"

    def test_groupby_benchmark(self):
        """Benchmark groupby operation performance."""
        logger.info("⚡ Benchmarking groupby operations...")

        sizes = [1000, 10000, 100000]

        for size in sizes:
            df = pd.DataFrame({
                'category': np.random.choice(['A', 'B', 'C', 'D'], size),
                'value1': np.random.randn(size),
                'value2': np.random.randn(size)
            })
            ldf = LineageDataFrame(df, table_name=f"groupby_test_{size}")

            def groupby_operation():
                return ldf.groupby('category').agg({
                    'value1': 'mean',
                    'value2': 'sum'
                }).reset_index()

            result = self.benchmarker.benchmark_operation(
                f"groupby_{size}", groupby_operation, size
            )

            print(f"📊 GroupBy {size:,} rows: {result.execution_time_ms:.2f}ms, "
                  f"{result.operations_per_second:.0f} ops/s")

            assert result.execution_time_ms < 5000, f"GroupBy too slow: {result.execution_time_ms}ms"

    def test_merge_benchmark(self):
        """Benchmark merge operation performance."""
        logger.info("⚡ Benchmarking merge operations...")

        sizes = [1000, 5000, 10000]  # Smaller for merge (O(n²) complexity)

        for size in sizes:
            df1 = pd.DataFrame({
                'key': range(size),
                'value1': np.random.randn(size)
            })
            df2 = pd.DataFrame({
                'key': range(0, size, 2),  # Half the keys
                'value2': np.random.randn(size // 2)
            })

            ldf1 = LineageDataFrame(df1, table_name=f"merge1_{size}")
            ldf2 = LineageDataFrame(df2, table_name=f"merge2_{size}")

            def merge_operation():
                return ldf1.merge(ldf2, on='key')

            result = self.benchmarker.benchmark_operation(
                f"merge_{size}", merge_operation, size
            )

            print(f"🔗 Merge {size:,} rows: {result.execution_time_ms:.2f}ms, "
                  f"{result.operations_per_second:.0f} ops/s")

            assert result.execution_time_ms < 10000, f"Merge too slow: {result.execution_time_ms}ms"


class TestScalabilityBenchmarks:
    """Test scalability characteristics."""

    def setup_method(self):
        """Setup for scalability tests."""
        self.benchmarker = PerformanceBenchmarker()

    def test_linear_scalability(self):
        """Test if operations scale linearly with data size."""
        logger.info("📈 Testing linear scalability...")

        base_sizes = [1000, 2000, 4000, 8000, 16000]
        scalability_results = {}

        for size in base_sizes:
            df = pd.DataFrame({
                'id': range(size),
                'value': np.random.randn(size),
                'category': np.random.choice(['A', 'B', 'C'], size)
            })
            ldf = LineageDataFrame(df, table_name=f"scale_{size}")

            def scalability_operation():
                # Create a copy to work with
                working_df = ldf.copy()

                # Apply operations that preserve data structure
                result = (working_df
                          .assign(doubled=working_df['value'] * 2)
                          .groupby('category')
                          .mean()
                          .reset_index())
                return result

            result = self.benchmarker.benchmark_operation(
                f"scalability_{size}", scalability_operation, size
            )

            scalability_results[size] = result
            print(f"📊 Size {size:,}: {result.execution_time_ms:.2f}ms")

        # Analyze scalability
        sizes = sorted(scalability_results.keys())
        for i in range(1, len(sizes)):
            current_size = sizes[i]
            prev_size = sizes[i-1]

            current_time = scalability_results[current_size].execution_time_ms
            prev_time = scalability_results[prev_size].execution_time_ms

            size_ratio = current_size / prev_size
            time_ratio = current_time / \
                prev_time if prev_time > 0 else float('inf')

            scalability_factor = time_ratio / size_ratio

            print(f"📈 {prev_size:,} → {current_size:,}: "
                  f"{size_ratio:.1f}x size, {time_ratio:.1f}x time, "
                  f"scalability factor: {scalability_factor:.2f}")

            # Good scalability should be close to 1.0 (linear)
            assert scalability_factor < 3.0, f"Poor scalability: {scalability_factor:.2f}"

    def test_memory_scalability(self):
        """Test memory usage scalability."""
        logger.info("🧠 Testing memory scalability...")

        sizes = [1000, 5000, 10000, 20000]
        memory_results = {}

        for size in sizes:
            df = pd.DataFrame({
                'data': np.random.randn(size),
                'text': [f'text_{i}' for i in range(size)]
            })

            def memory_operation():
                ldf = LineageDataFrame(df, table_name=f"memory_{size}")
                return ldf.assign(processed=ldf['data'] * 2)

            result = self.benchmarker.benchmark_operation(
                f"memory_{size}", memory_operation, size
            )

            memory_results[size] = result
            print(f"🧠 Size {size:,}: {result.memory_per_row_kb:.3f}KB/row, "
                  f"total: {result.memory_delta_mb:.1f}MB")

        # Memory should scale roughly linearly
        memory_per_row_values = [
            r.memory_per_row_kb for r in memory_results.values()]
        memory_variance = np.var(memory_per_row_values)

        print(f"📊 Memory per row variance: {memory_variance:.6f}")
        assert memory_variance < 1.0, f"High memory variance: {memory_variance:.6f}"


class TestConcurrencyBenchmarks:
    """Test concurrent performance."""

    def setup_method(self):
        """Setup for concurrency tests."""
        self.benchmarker = PerformanceBenchmarker()

    def test_concurrent_throughput(self):
        """Test throughput under concurrent load."""
        logger.info("🔄 Testing concurrent throughput...")

        def worker_operation(worker_id: int) -> Tuple[int, float]:
            """Single worker operation."""
            df = pd.DataFrame({
                'id': range(1000),
                'value': np.random.randn(1000),
                'worker': worker_id
            })

            start_time = time.perf_counter()
            ldf = LineageDataFrame(df, table_name=f"concurrent_{worker_id}")
            result = ldf.assign(processed=ldf['value'] * worker_id)
            end_time = time.perf_counter()

            return worker_id, (end_time - start_time) * 1000  # ms

        # Test different concurrency levels
        concurrency_levels = [1, 2, 4, 8, 16]

        for num_workers in concurrency_levels:
            print(f"🔄 Testing {num_workers} concurrent workers...")

            start_time = time.perf_counter()

            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(worker_operation, i)
                           for i in range(num_workers)]
                results = [future.result() for future in futures]

            end_time = time.perf_counter()

            total_time = (end_time - start_time) * 1000  # ms
            individual_times = [time_ms for _, time_ms in results]
            avg_individual_time = np.mean(individual_times)
            throughput = num_workers / \
                (total_time / 1000)  # operations per second

            print(f"  ⚡ Total time: {total_time:.2f}ms")
            print(f"  ⚡ Avg individual: {avg_individual_time:.2f}ms")
            print(f"  ⚡ Throughput: {throughput:.1f} ops/s")

            # Throughput should increase with more workers (up to CPU limit)
            if num_workers <= psutil.cpu_count():
                expected_min_throughput = num_workers * 0.5  # Allow 50% efficiency
                assert throughput >= expected_min_throughput, \
                    f"Low throughput: {throughput:.1f} < {expected_min_throughput:.1f}"


class TestRegressionBenchmarks:
    """Test for performance regressions."""

    def setup_method(self):
        """Setup for regression tests."""
        self.benchmarker = PerformanceBenchmarker()

    def test_baseline_performance(self):
        """Establish baseline performance metrics."""
        logger.info("📏 Establishing baseline performance...")

        # Standard test case
        df = pd.DataFrame({
            'id': range(10000),
            'value': np.random.randn(10000),
            'category': np.random.choice(['A', 'B', 'C'], 10000)
        })

        def baseline_operation():
            ldf = LineageDataFrame(df, table_name="baseline")
            # Create a copy to work with
            working_df = ldf.copy()

            return (working_df
                    .assign(squared=working_df['value'] ** 2)
                    .groupby('category')
                    .mean()
                    .reset_index())

        result = self.benchmarker.benchmark_operation(
            "baseline", baseline_operation, 10000
        )

        # Define baseline expectations (these should be conservative)
        baseline_expectations = {
            'max_time_ms': 2000,  # 2 seconds max
            'max_memory_per_row_kb': 5.0,  # 5KB per row max
            'min_ops_per_second': 0.5  # At least 0.5 ops/s
        }

        print(f"📊 Baseline Results:")
        print(
            f"  ⏱️  Time: {result.execution_time_ms:.2f}ms (max: {baseline_expectations['max_time_ms']}ms)")
        print(
            f"  🧠 Memory: {result.memory_per_row_kb:.3f}KB/row (max: {baseline_expectations['max_memory_per_row_kb']}KB)")
        print(
            f"  ⚡ Speed: {result.operations_per_second:.2f} ops/s (min: {baseline_expectations['min_ops_per_second']})")

        # Regression assertions
        assert result.execution_time_ms <= baseline_expectations['max_time_ms'], \
            f"Performance regression: {result.execution_time_ms}ms > {baseline_expectations['max_time_ms']}ms"

        assert result.memory_per_row_kb <= baseline_expectations['max_memory_per_row_kb'], \
            f"Memory regression: {result.memory_per_row_kb}KB > {baseline_expectations['max_memory_per_row_kb']}KB"

        assert result.operations_per_second >= baseline_expectations['min_ops_per_second'], \
            f"Speed regression: {result.operations_per_second} < {baseline_expectations['min_ops_per_second']}"

        print("✅ Baseline performance within acceptable limits")


def run_benchmark_suite():
    """Run the complete benchmark suite."""
    print("⚡" * 20)
    print("COMPREHENSIVE BENCHMARK SUITE")
    print("Performance Analysis of DataLineagePy")
    print("⚡" * 20)

    benchmark_classes = [
        TestOperationBenchmarks,
        TestScalabilityBenchmarks,
        TestConcurrencyBenchmarks,
        TestRegressionBenchmarks
    ]

    total_start = time.time()
    all_results = {}

    for benchmark_class in benchmark_classes:
        class_name = benchmark_class.__name__
        print(f"\n⚡ Running {class_name}...")

        try:
            benchmark_instance = benchmark_class()
            class_results = {}

            # Get benchmark methods
            benchmark_methods = [method for method in dir(benchmark_instance)
                                 if method.startswith('test_') and callable(getattr(benchmark_instance, method))]

            for method_name in benchmark_methods:
                try:
                    if hasattr(benchmark_instance, 'setup_method'):
                        benchmark_instance.setup_method()

                    method = getattr(benchmark_instance, method_name)
                    start = time.time()
                    method()
                    end = time.time()

                    class_results[method_name] = {
                        'status': 'COMPLETED',
                        'time': end - start
                    }
                    print(f"  ✅ {method_name}: COMPLETED ({end-start:.2f}s)")

                except Exception as e:
                    class_results[method_name] = {
                        'status': 'FAILED',
                        'error': str(e),
                        'time': time.time() - start if 'start' in locals() else 0
                    }
                    print(f"  ❌ {method_name}: FAILED - {e}")

            all_results[class_name] = class_results

        except Exception as e:
            print(f"  ☠️  {class_name} completely failed: {e}")
            all_results[class_name] = {'TOTAL_FAILURE': str(e)}

    total_end = time.time()

    # Generate benchmark report
    print("\n" + "="*60)
    print("⚡ BENCHMARK SUITE RESULTS ⚡")
    print("="*60)

    total_benchmarks = sum(len(cr)
                           for cr in all_results.values() if isinstance(cr, dict))
    completed_benchmarks = sum(1 for cr in all_results.values()
                               if isinstance(cr, dict)
                               for r in cr.values()
                               if isinstance(r, dict) and r.get('status') == 'COMPLETED')

    print(f"⏱️  Total benchmark time: {total_end - total_start:.2f} seconds")
    print(f"🧪 Benchmarks run: {total_benchmarks}")
    print(f"✅ Benchmarks completed: {completed_benchmarks}")
    print(f"❌ Benchmarks failed: {total_benchmarks - completed_benchmarks}")
    print(
        f"📊 Completion rate: {(completed_benchmarks/total_benchmarks)*100:.1f}%")

    # Performance summary
    print(f"\n⚡ PERFORMANCE SUMMARY:")

    for class_name, results in all_results.items():
        if isinstance(results, dict) and len(results) > 0:
            completed = sum(1 for r in results.values()
                            if isinstance(r, dict) and r.get('status') == 'COMPLETED')
            total = len(results)
            avg_time = np.mean([r['time'] for r in results.values()
                               if isinstance(r, dict) and 'time' in r])

            print(
                f"  {class_name}: {completed}/{total} completed, avg: {avg_time:.2f}s")

    # Final performance verdict
    if completed_benchmarks == total_benchmarks:
        print(f"\n🏆 PERFORMANCE VERDICT: EXCELLENT!")
        print("⚡ All benchmarks completed successfully!")
    elif completed_benchmarks / total_benchmarks >= 0.9:
        print(f"\n🎯 PERFORMANCE VERDICT: GOOD!")
        print("⚡ Most benchmarks completed successfully!")
    else:
        print(f"\n⚠️  PERFORMANCE VERDICT: NEEDS OPTIMIZATION!")
        print("🔧 Some performance issues detected.")

    return all_results


if __name__ == "__main__":
    run_benchmark_suite()
