"""
Benchmarking utilities for performance testing and scalability analysis.
"""

import time
import statistics
from typing import Dict, List, Any, Callable, Optional, Tuple
from dataclasses import dataclass
from ..core.tracker import LineageTracker
from .generators import TestDataGenerator


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    operations_per_second: float
    memory_usage_mb: Optional[float] = None
    success_rate: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'iterations': self.iterations,
            'total_time': self.total_time,
            'avg_time': self.avg_time,
            'min_time': self.min_time,
            'max_time': self.max_time,
            'std_dev': self.std_dev,
            'operations_per_second': self.operations_per_second,
            'memory_usage_mb': self.memory_usage_mb,
            'success_rate': self.success_rate
        }


class LineageBenchmark:
    """
    Benchmark suite for lineage tracking operations.
    """

    def __init__(self):
        """Initialize the benchmark suite."""
        self.results = []
        self.generator = TestDataGenerator(seed=42)  # Reproducible results

    def benchmark_function(self,
                           func: Callable,
                           name: str,
                           iterations: int = 100,
                           warmup_iterations: int = 10) -> BenchmarkResult:
        """
        Benchmark a function with multiple iterations.

        Args:
            func: Function to benchmark
            name: Name of the benchmark
            iterations: Number of iterations to run
            warmup_iterations: Number of warmup iterations

        Returns:
            BenchmarkResult with timing statistics
        """
        # Warmup
        for _ in range(warmup_iterations):
            try:
                func()
            except Exception:
                pass

        # Actual benchmark
        times = []
        successes = 0

        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                func()
                successes += 1
            except Exception:
                pass
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        # Calculate statistics
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        ops_per_second = iterations / total_time if total_time > 0 else 0
        success_rate = successes / iterations

        # Memory usage (if available)
        memory_usage = None
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_usage = process.memory_info().rss / 1024 / 1024
        except ImportError:
            pass

        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            operations_per_second=ops_per_second,
            memory_usage_mb=memory_usage,
            success_rate=success_rate
        )

        self.results.append(result)
        return result

    def benchmark_dataframe_creation(self, rows: int = 1000) -> BenchmarkResult:
        """
        Benchmark DataFrame creation with lineage tracking.

        Args:
            rows: Number of rows in test DataFrame

        Returns:
            BenchmarkResult for DataFrame creation
        """
        def create_dataframe():
            return self.generator.generate_simple_dataframe(rows=rows)

        return self.benchmark_function(
            create_dataframe,
            f"dataframe_creation_{rows}_rows",
            iterations=50
        )

    def benchmark_column_operations(self, rows: int = 1000) -> BenchmarkResult:
        """
        Benchmark column operations with lineage tracking.

        Args:
            rows: Number of rows in test DataFrame

        Returns:
            BenchmarkResult for column operations
        """
        df = self.generator.generate_simple_dataframe(rows=rows)

        def column_operations():
            # Column selection
            _ = df['A']
            # Column assignment
            df['E'] = df['A'] + df['B']
            # Column calculation
            df['F'] = df['C'] * 2

        return self.benchmark_function(
            column_operations,
            f"column_operations_{rows}_rows",
            iterations=100
        )

    def benchmark_merge_operations(self, rows: int = 1000) -> BenchmarkResult:
        """
        Benchmark merge operations with lineage tracking.

        Args:
            rows: Number of rows in test DataFrames

        Returns:
            BenchmarkResult for merge operations
        """
        df1 = self.generator.generate_simple_dataframe(name="df1", rows=rows)
        df2 = self.generator.generate_simple_dataframe(name="df2", rows=rows)

        def merge_operations():
            return df1.merge(df2, left_on='A', right_on='A', how='inner')

        return self.benchmark_function(
            merge_operations,
            f"merge_operations_{rows}_rows",
            iterations=50
        )

    def benchmark_groupby_operations(self, rows: int = 1000) -> BenchmarkResult:
        """
        Benchmark groupby operations with lineage tracking.

        Args:
            rows: Number of rows in test DataFrame

        Returns:
            BenchmarkResult for groupby operations
        """
        df = self.generator.generate_simple_dataframe(rows=rows)

        def groupby_operations():
            return df.groupby('A').agg({'B': 'sum', 'C': 'mean'})

        return self.benchmark_function(
            groupby_operations,
            f"groupby_operations_{rows}_rows",
            iterations=50
        )


class PerformanceBenchmark:
    """
    Performance benchmark for overall system performance.
    """

    def __init__(self):
        """Initialize the performance benchmark."""
        self.results = []

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """
        Run a comprehensive performance benchmark.

        Returns:
            Dictionary with comprehensive benchmark results
        """
        benchmark = LineageBenchmark()

        # Test different data sizes
        data_sizes = [100, 1000, 5000]

        results = {
            'dataframe_creation': {},
            'column_operations': {},
            'merge_operations': {},
            'groupby_operations': {},
            'summary': {}
        }

        for size in data_sizes:
            # DataFrame creation
            result = benchmark.benchmark_dataframe_creation(rows=size)
            results['dataframe_creation'][size] = result.to_dict()

            # Column operations
            result = benchmark.benchmark_column_operations(rows=size)
            results['column_operations'][size] = result.to_dict()

            # Merge operations
            result = benchmark.benchmark_merge_operations(rows=size)
            results['merge_operations'][size] = result.to_dict()

            # GroupBy operations
            result = benchmark.benchmark_groupby_operations(rows=size)
            results['groupby_operations'][size] = result.to_dict()

        # Calculate summary statistics
        all_results = benchmark.results
        results['summary'] = {
            'total_benchmarks': len(all_results),
            'avg_operations_per_second': statistics.mean([r.operations_per_second for r in all_results]),
            'avg_success_rate': statistics.mean([r.success_rate for r in all_results]),
            'total_time': sum([r.total_time for r in all_results])
        }

        return results


class ScalabilityTest:
    """
    Test scalability characteristics of lineage tracking.
    """

    def __init__(self):
        """Initialize the scalability test."""
        self.generator = TestDataGenerator(seed=42)

    def test_node_scalability(self, max_nodes: int = 10000) -> Dict[str, Any]:
        """
        Test how performance scales with number of nodes.

        Args:
            max_nodes: Maximum number of nodes to test

        Returns:
            Scalability test results
        """
        node_counts = [100, 500, 1000, 2500, 5000, max_nodes]
        results = []

        for node_count in node_counts:
            # Clear tracker
            tracker = LineageTracker.get_global_instance()
            tracker.clear()

            start_time = time.perf_counter()

            # Create DataFrames to generate nodes
            # Approximate nodes per DataFrame
            num_dataframes = max(1, node_count // 10)
            dataframes = []

            for i in range(num_dataframes):
                df = self.generator.generate_simple_dataframe(
                    name=f"df_{i}",
                    rows=100,
                    columns=[f'col_{j}' for j in range(5)]
                )
                dataframes.append(df)

                # Perform some operations to create more nodes
                if i > 0:
                    df_merged = dataframes[0].merge(
                        df, left_on='col_0', right_on='col_0', how='inner')

            end_time = time.perf_counter()

            actual_nodes = len(tracker.nodes)
            actual_edges = len(tracker.edges)

            results.append({
                'target_nodes': node_count,
                'actual_nodes': actual_nodes,
                'actual_edges': actual_edges,
                'time_taken': end_time - start_time,
                'nodes_per_second': actual_nodes / (end_time - start_time) if end_time > start_time else 0
            })

        return {
            'test_name': 'node_scalability',
            'results': results,
            'scalability_factor': self._calculate_scalability_factor(results)
        }

    def test_operation_scalability(self, max_operations: int = 1000) -> Dict[str, Any]:
        """
        Test how performance scales with number of operations.

        Args:
            max_operations: Maximum number of operations to test

        Returns:
            Operation scalability test results
        """
        # Use smaller operation counts to avoid hitting node limits
        operation_counts = [5, 10, 15, 20, 25, min(30, max_operations)]
        results = []

        for op_count in operation_counts:
            # Clear tracker
            tracker = LineageTracker.get_global_instance()
            tracker.clear()

            df = self.generator.generate_simple_dataframe(
                rows=100)  # Smaller dataset

            start_time = time.perf_counter()

            # Perform operations
            for i in range(op_count):
                col_name = f'calc_{i}'
                df = df.assign(**{col_name: lambda x, i=i: x['A'] + i})

            end_time = time.perf_counter()

            actual_nodes = len(tracker.nodes)
            actual_edges = len(tracker.edges)

            results.append({
                'operations': op_count,
                'nodes_created': actual_nodes,
                'edges_created': actual_edges,
                'time_taken': end_time - start_time,
                'operations_per_second': op_count / (end_time - start_time) if end_time > start_time else 0
            })

        return {
            'test_name': 'operation_scalability',
            'results': results,
            'scalability_factor': self._calculate_scalability_factor(results, 'operations_per_second')
        }

    def _calculate_scalability_factor(self, results: List[Dict], metric: str = 'nodes_per_second') -> float:
        """
        Calculate scalability factor (how well performance scales).

        Args:
            results: List of test results
            metric: Metric to analyze for scalability

        Returns:
            Scalability factor (1.0 = linear scaling, <1.0 = degrading performance)
        """
        if len(results) < 2:
            return 1.0

        # Compare first and last results
        first_result = results[0]
        last_result = results[-1]

        first_metric = first_result.get(metric, 0)
        last_metric = last_result.get(metric, 0)

        if first_metric == 0:
            return 1.0

        # Calculate relative performance
        performance_ratio = last_metric / first_metric

        # Calculate size ratio
        if 'target_nodes' in first_result:
            size_ratio = last_result['target_nodes'] / \
                first_result['target_nodes']
        elif 'operations' in first_result:
            size_ratio = last_result['operations'] / first_result['operations']
        else:
            size_ratio = 1.0

        # Scalability factor: 1.0 = perfect linear scaling
        scalability_factor = performance_ratio / size_ratio if size_ratio > 0 else 0.0

        return max(0.0, min(1.0, scalability_factor))  # Clamp between 0 and 1
