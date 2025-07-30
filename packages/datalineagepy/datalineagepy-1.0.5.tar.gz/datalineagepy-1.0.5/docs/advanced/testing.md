# Testing Framework Complete Guide

DataLineagePy includes a comprehensive testing framework to ensure your lineage tracking is accurate, complete, and performant.

## 🎯 Overview

The testing framework provides:

- **Lineage Validation** - Verify graph integrity and correctness
- **Quality Validation** - Check coverage and completeness
- **Performance Benchmarking** - Measure speed and memory usage
- **Schema Validation** - Ensure column consistency
- **Anomaly Detection** - Statistical and ML-based detection
- **Test Data Generation** - Create realistic test datasets

## 📚 Testing Components

### Core Testing Modules

```python
from lineagepy.testing import (
    LineageValidator,
    QualityValidator,
    PerformanceValidator,
    SchemaValidator,
    TestDataGenerator,
    PerformanceBenchmark,
    AnomalyDetector
)
```

---

## 🔍 LineageValidator

Validates lineage graph integrity and correctness.

### Constructor

```python
validator = LineageValidator(tracker, config=None)
```

**Configuration Options:**

```python
config = {
    'strict_mode': True,
    'check_cycles': True,
    'validate_metadata': True,
    'check_orphaned_nodes': False,  # Updated to be smarter
    'max_depth': 100
}
```

### Core Validation Methods

#### `validate_all()`

Comprehensive validation of entire lineage graph.

**Returns:**

- `dict`: Validation results containing:
  - `is_valid` (bool): Overall validation status
  - `issues` (list): List of validation issues
  - `warnings` (list): Non-critical warnings
  - `stats` (dict): Validation statistics

**Example:**

```python
results = validator.validate_all()
if results['is_valid']:
    print("✅ Lineage is valid!")
else:
    print("❌ Issues found:")
    for issue in results['issues']:
        print(f"  - {issue}")
```

#### `validate_graph_integrity()`

Check basic graph structure and consistency.

**Validates:**

- No circular dependencies
- All edges have valid source/target nodes
- Node types are consistent
- Required metadata is present

**Returns:**

- `dict`: Integrity validation results

**Example:**

```python
integrity = validator.validate_graph_integrity()
print(f"Graph integrity: {integrity['status']}")
```

#### `validate_dag_structure()`

Ensure the graph is a directed acyclic graph (DAG).

**Returns:**

- `dict`: DAG validation results with cycle detection

**Example:**

```python
dag_results = validator.validate_dag_structure()
if dag_results['has_cycles']:
    print(f"Cycles detected: {dag_results['cycles']}")
```

#### `validate_node_consistency()`

Check consistency of nodes and their relationships.

**Validates:**

- Node naming conventions
- Metadata consistency
- Type consistency
- Reference integrity

**Example:**

```python
consistency = validator.validate_node_consistency()
for warning in consistency['warnings']:
    print(f"⚠️ {warning}")
```

#### `validate_operation_lineage(column_name)`

Validate lineage for a specific column.

**Parameters:**

- `column_name` (str): Column to validate

**Returns:**

- `dict`: Column-specific validation results

**Example:**

```python
column_validation = validator.validate_operation_lineage('profit')
print(f"Profit lineage valid: {column_validation['is_valid']}")
```

### Advanced Validation Methods

#### `check_lineage_completeness()`

Verify that all expected lineage relationships are captured.

**Returns:**

- `dict`: Completeness analysis

**Example:**

```python
completeness = validator.check_lineage_completeness()
print(f"Coverage: {completeness['coverage_percentage']:.1%}")
```

#### `validate_metadata_consistency()`

Check consistency of metadata across related nodes.

**Example:**

```python
metadata_check = validator.validate_metadata_consistency()
for inconsistency in metadata_check['inconsistencies']:
    print(f"Metadata issue: {inconsistency}")
```

#### `detect_orphaned_nodes()`

Find nodes with no connections (now smarter about column nodes).

**Returns:**

- `dict`: Orphaned nodes analysis with context

**Example:**

```python
orphaned = validator.detect_orphaned_nodes()
print(f"Problematic orphaned nodes: {orphaned['problematic_nodes']}")
print(f"Normal unused columns: {orphaned['unused_columns']}")
```

### Custom Validation Rules

#### `add_custom_rule(rule_name, rule_function)`

Add custom validation logic.

**Parameters:**

- `rule_name` (str): Name for the rule
- `rule_function` (callable): Function that returns validation result

**Example:**

```python
def validate_business_rules(tracker):
    # Custom business logic validation
    issues = []
    if not tracker.has_column('customer_id'):
        issues.append("Missing required customer_id column")
    return {'passed': len(issues) == 0, 'issues': issues}

validator.add_custom_rule('business_rules', validate_business_rules)
```

---

## 📊 QualityValidator

Validates data quality aspects of lineage tracking.

### Constructor

```python
quality_validator = QualityValidator(tracker, config=None)
```

### Quality Assessment Methods

#### `calculate_coverage()`

Calculate lineage coverage across the pipeline.

**Returns:**

- `float`: Coverage percentage (0.0 to 1.0)

**Example:**

```python
coverage = quality_validator.calculate_coverage()
print(f"Lineage coverage: {coverage:.1%}")
```

#### `check_completeness()`

Assess completeness of lineage documentation.

**Returns:**

- `dict`: Completeness metrics

**Example:**

```python
completeness = quality_validator.check_completeness()
print(f"Documentation completeness: {completeness['score']:.1%}")
```

#### `analyze_quality_metrics()`

Comprehensive quality analysis.

**Returns:**

- `dict`: Quality metrics including:
  - `coverage_score`: Lineage coverage
  - `completeness_score`: Documentation completeness
  - `accuracy_score`: Lineage accuracy
  - `consistency_score`: Metadata consistency

**Example:**

```python
metrics = quality_validator.analyze_quality_metrics()
for metric, score in metrics.items():
    print(f"{metric}: {score:.1%}")
```

#### `validate_column_coverage()`

Check coverage for individual columns.

**Returns:**

- `dict`: Per-column coverage analysis

**Example:**

```python
column_coverage = quality_validator.validate_column_coverage()
for col, coverage in column_coverage.items():
    print(f"{col}: {coverage:.1%} coverage")
```

### Quality Rules and Checks

#### `add_quality_rule(column_name, rule_type, rule_description, **metadata)`

Add a quality rule for validation.

**Parameters:**

- `column_name` (str): Column name
- `rule_type` (str): Type of quality rule
- `rule_description` (str): Human-readable description
- `**metadata`: Additional rule metadata

**Example:**

```python
quality_validator.add_quality_rule(
    'email',
    'format_validation',
    'Must be valid email format',
    regex=r'^[^@]+@[^@]+\.[^@]+$',
    expected_pass_rate=0.95
)
```

#### `validate_quality_rules()`

Validate all registered quality rules.

**Returns:**

- `dict`: Quality rule validation results

**Example:**

```python
rule_results = quality_validator.validate_quality_rules()
for rule, result in rule_results.items():
    status = "✅" if result['passed'] else "❌"
    print(f"{status} {rule}: {result['description']}")
```

---

## ⚡ PerformanceValidator

Validates performance characteristics of lineage tracking.

### Constructor

```python
perf_validator = PerformanceValidator(tracker, config=None)
```

### Performance Assessment Methods

#### `measure_tracking_overhead()`

Measure the overhead of lineage tracking.

**Returns:**

- `dict`: Performance overhead metrics

**Example:**

```python
overhead = perf_validator.measure_tracking_overhead()
print(f"Tracking overhead: {overhead['overhead_percentage']:.1%}")
print(f"Average operation time: {overhead['avg_operation_time_ms']:.2f}ms")
```

#### `benchmark_operations(operation_types=None)`

Benchmark specific types of operations.

**Parameters:**

- `operation_types` (list, optional): Specific operations to benchmark

**Returns:**

- `dict`: Operation performance benchmarks

**Example:**

```python
benchmarks = perf_validator.benchmark_operations(['filter', 'groupby', 'merge'])
for op_type, metrics in benchmarks.items():
    print(f"{op_type}: {metrics['avg_time_ms']:.2f}ms")
```

#### `analyze_memory_usage()`

Analyze memory consumption patterns.

**Returns:**

- `dict`: Memory usage analysis

**Example:**

```python
memory_analysis = perf_validator.analyze_memory_usage()
print(f"Total memory usage: {memory_analysis['total_mb']:.1f}MB")
print(f"Memory per node: {memory_analysis['memory_per_node_kb']:.1f}KB")
```

#### `validate_performance_requirements(requirements)`

Validate against performance requirements.

**Parameters:**

- `requirements` (dict): Performance requirements to validate against

**Example:**

```python
requirements = {
    'max_operation_time_ms': 100,
    'max_memory_mb': 500,
    'max_overhead_percentage': 10
}

perf_results = perf_validator.validate_performance_requirements(requirements)
print(f"Performance requirements met: {perf_results['all_passed']}")
```

### Scalability Testing

#### `test_scalability(dataset_sizes)`

Test performance across different dataset sizes.

**Parameters:**

- `dataset_sizes` (list): List of dataset sizes to test

**Returns:**

- `dict`: Scalability test results

**Example:**

```python
scalability = perf_validator.test_scalability([1000, 10000, 100000])
for size, metrics in scalability.items():
    print(f"Size {size}: {metrics['time_ms']:.2f}ms, {metrics['memory_mb']:.1f}MB")
```

---

## 🔧 SchemaValidator

Validates schema consistency and evolution.

### Constructor

```python
schema_validator = SchemaValidator(tracker, config=None)
```

### Schema Validation Methods

#### `validate_column_consistency()`

Check consistency of column definitions across lineage.

**Returns:**

- `dict`: Column consistency results

**Example:**

```python
consistency = schema_validator.validate_column_consistency()
for issue in consistency['inconsistencies']:
    print(f"Schema issue: {issue}")
```

#### `detect_schema_drift(baseline_schema)`

Detect changes in schema over time.

**Parameters:**

- `baseline_schema` (dict): Reference schema to compare against

**Returns:**

- `dict`: Schema drift analysis

**Example:**

```python
drift = schema_validator.detect_schema_drift(baseline_schema)
print(f"Schema drift detected: {drift['has_drift']}")
```

#### `validate_data_types()`

Validate data type consistency in lineage.

**Returns:**

- `dict`: Data type validation results

**Example:**

```python
type_validation = schema_validator.validate_data_types()
for column, issues in type_validation['issues'].items():
    print(f"{column}: {issues}")
```

---

## 🧪 TestDataGenerator

Generates realistic test data for validation and benchmarking.

### Constructor

```python
data_generator = TestDataGenerator(config=None)
```

### Test Data Generation

#### `generate_customers(n_rows)`

Generate realistic customer data.

**Parameters:**

- `n_rows` (int): Number of customer records

**Returns:**

- `pd.DataFrame`: Generated customer data

**Example:**

```python
customers = data_generator.generate_customers(1000)
# Columns: customer_id, name, email, age, country, registration_date
```

#### `generate_orders(customers_df, orders_per_customer)`

Generate order data linked to customers.

**Parameters:**

- `customers_df` (pd.DataFrame): Customer data
- `orders_per_customer` (tuple): Min/max orders per customer

**Returns:**

- `pd.DataFrame`: Generated order data

**Example:**

```python
orders = data_generator.generate_orders(customers, (1, 5))
# Columns: order_id, customer_id, product, amount, order_date
```

#### `generate_products(n_products)`

Generate product catalog data.

**Parameters:**

- `n_products` (int): Number of products

**Returns:**

- `pd.DataFrame`: Generated product data

**Example:**

```python
products = data_generator.generate_products(100)
# Columns: product_id, name, category, price, description
```

#### `generate_time_series(start_date, end_date, frequency)`

Generate time series data.

**Parameters:**

- `start_date` (str): Start date
- `end_date` (str): End date
- `frequency` (str): Data frequency ('D', 'H', etc.)

**Returns:**

- `pd.DataFrame`: Time series data

**Example:**

```python
ts_data = data_generator.generate_time_series('2024-01-01', '2024-12-31', 'D')
# Columns: date, value, trend, seasonal, noise
```

### Edge Case Generation

#### `generate_edge_cases()`

Generate data with common edge cases.

**Returns:**

- `dict`: Various edge case datasets

**Example:**

```python
edge_cases = data_generator.generate_edge_cases()
null_heavy = edge_cases['high_nulls']  # Data with many nulls
duplicates = edge_cases['duplicates']   # Data with duplicates
outliers = edge_cases['outliers']      # Data with outliers
```

#### `generate_schema_evolution_data()`

Generate data showing schema changes over time.

**Returns:**

- `list`: Series of DataFrames showing schema evolution

**Example:**

```python
evolution = data_generator.generate_schema_evolution_data()
for i, df in enumerate(evolution):
    print(f"Schema version {i}: {df.columns.tolist()}")
```

---

## 📈 PerformanceBenchmark

Comprehensive performance benchmarking suite.

### Constructor

```python
benchmark = PerformanceBenchmark(tracker, config=None)
```

### Benchmarking Methods

#### `run_comprehensive_benchmark()`

Execute full performance benchmark suite.

**Returns:**

- `dict`: Comprehensive benchmark results

**Example:**

```python
results = benchmark.run_comprehensive_benchmark()
print(f"Overall performance score: {results['overall_score']}")
```

#### `benchmark_operations()`

Benchmark individual operations.

**Returns:**

- `dict`: Operation-specific benchmarks

**Example:**

```python
op_benchmarks = benchmark.benchmark_operations()
for operation, metrics in op_benchmarks.items():
    print(f"{operation}: {metrics['ops_per_second']:.0f} ops/sec")
```

#### `memory_benchmark()`

Comprehensive memory usage benchmark.

**Returns:**

- `dict`: Memory benchmark results

**Example:**

```python
memory_bench = benchmark.memory_benchmark()
print(f"Peak memory: {memory_bench['peak_memory_mb']:.1f}MB")
```

#### `scalability_benchmark(test_sizes)`

Test performance scalability.

**Parameters:**

- `test_sizes` (list): Dataset sizes to test

**Returns:**

- `dict`: Scalability benchmark results

**Example:**

```python
scalability = benchmark.scalability_benchmark([1000, 10000, 50000])
for size, result in scalability.items():
    print(f"Size {size}: {result['time_per_operation_ms']:.3f}ms/op")
```

### Report Generation

#### `generate_report(output_file)`

Generate comprehensive performance report.

**Parameters:**

- `output_file` (str): Path to save HTML report

**Example:**

```python
benchmark.generate_report('performance_report.html')
```

#### `compare_with_baseline(baseline_results)`

Compare current performance with baseline.

**Parameters:**

- `baseline_results` (dict): Previous benchmark results

**Returns:**

- `dict`: Performance comparison

**Example:**

```python
comparison = benchmark.compare_with_baseline(previous_results)
print(f"Performance change: {comparison['overall_change']:.1%}")
```

---

## 🤖 AnomalyDetector

ML-powered anomaly detection for data lineage.

### Constructor

```python
detector = AnomalyDetector(tracker, config=None)
```

### Statistical Anomaly Detection

#### `detect_statistical_anomalies()`

Detect anomalies using statistical methods.

**Returns:**

- `dict`: Statistical anomaly detection results

**Example:**

```python
statistical = detector.detect_statistical_anomalies()
for anomaly in statistical['anomalies']:
    print(f"Statistical anomaly: {anomaly['description']}")
```

#### `detect_outliers(column_name, method='zscore')`

Detect outliers in specific columns.

**Parameters:**

- `column_name` (str): Column to analyze
- `method` (str): Detection method ('zscore', 'iqr', 'isolation_forest')

**Returns:**

- `dict`: Outlier detection results

**Example:**

```python
outliers = detector.detect_outliers('transaction_amount', 'zscore')
print(f"Found {len(outliers['outlier_indices'])} outliers")
```

### ML-Based Detection

#### `detect_ml_anomalies()`

Detect anomalies using machine learning models.

**Returns:**

- `dict`: ML-based anomaly detection results

**Example:**

```python
ml_anomalies = detector.detect_ml_anomalies()
for anomaly in ml_anomalies['anomalies']:
    print(f"ML anomaly (confidence: {anomaly['confidence']:.2f}): {anomaly['description']}")
```

#### `train_anomaly_model(training_data)`

Train custom anomaly detection model.

**Parameters:**

- `training_data` (pd.DataFrame): Training data

**Returns:**

- `object`: Trained model

**Example:**

```python
model = detector.train_anomaly_model(historical_data)
detector.set_custom_model(model)
```

### Pattern Detection

#### `detect_data_quality_issues()`

Detect data quality patterns and issues.

**Returns:**

- `dict`: Data quality issue detection

**Example:**

```python
quality_issues = detector.detect_data_quality_issues()
for issue in quality_issues['issues']:
    print(f"Quality issue: {issue['type']} - {issue['description']}")
```

#### `detect_lineage_anomalies()`

Detect unusual patterns in lineage structure.

**Returns:**

- `dict`: Lineage anomaly detection

**Example:**

```python
lineage_anomalies = detector.detect_lineage_anomalies()
for anomaly in lineage_anomalies['structural_anomalies']:
    print(f"Lineage anomaly: {anomaly}")
```

---

## 🧪 Complete Testing Workflows

### Basic Validation Workflow

```python
from lineagepy.testing import LineageValidator, QualityValidator

# Initialize validators
lineage_validator = LineageValidator(tracker)
quality_validator = QualityValidator(tracker)

# Run basic validation
lineage_results = lineage_validator.validate_all()
quality_results = quality_validator.analyze_quality_metrics()

# Check results
if lineage_results['is_valid'] and quality_results['coverage_score'] > 0.8:
    print("✅ Pipeline validation passed!")
else:
    print("❌ Validation issues found")
    print(f"Lineage issues: {lineage_results['issues']}")
    print(f"Coverage: {quality_results['coverage_score']:.1%}")
```

### Performance Testing Workflow

```python
from lineagepy.testing import PerformanceBenchmark, PerformanceValidator

# Run performance tests
benchmark = PerformanceBenchmark(tracker)
perf_validator = PerformanceValidator(tracker)

# Benchmark operations
benchmark_results = benchmark.run_comprehensive_benchmark()
overhead = perf_validator.measure_tracking_overhead()

# Check against requirements
requirements = {
    'max_operation_time_ms': 50,
    'max_memory_mb': 100,
    'max_overhead_percentage': 5
}

perf_check = perf_validator.validate_performance_requirements(requirements)

print(f"Performance requirements met: {perf_check['all_passed']}")
benchmark.generate_report('performance_report.html')
```

### Comprehensive Testing Suite

```python
from lineagepy.testing import *

def run_full_test_suite(tracker):
    """Run complete testing suite"""

    results = {}

    # 1. Lineage validation
    lineage_validator = LineageValidator(tracker)
    results['lineage'] = lineage_validator.validate_all()

    # 2. Quality validation
    quality_validator = QualityValidator(tracker)
    results['quality'] = quality_validator.analyze_quality_metrics()

    # 3. Performance validation
    perf_validator = PerformanceValidator(tracker)
    results['performance'] = perf_validator.measure_tracking_overhead()

    # 4. Schema validation
    schema_validator = SchemaValidator(tracker)
    results['schema'] = schema_validator.validate_column_consistency()

    # 5. Anomaly detection
    detector = AnomalyDetector(tracker)
    results['anomalies'] = detector.detect_statistical_anomalies()

    # 6. Generate comprehensive report
    generate_test_report(results, 'test_suite_report.html')

    return results

# Run the full suite
test_results = run_full_test_suite(tracker)
```

### Continuous Integration Testing

```python
def ci_validation_pipeline(tracker):
    """CI/CD validation pipeline"""

    # Quick validation for CI
    validator = LineageValidator(tracker, config={
        'strict_mode': True,
        'quick_mode': True  # Skip expensive checks
    })

    results = validator.validate_all()

    if not results['is_valid']:
        # Fail CI if validation fails
        raise ValidationError(f"Lineage validation failed: {results['issues']}")

    # Performance regression check
    perf_validator = PerformanceValidator(tracker)
    overhead = perf_validator.measure_tracking_overhead()

    if overhead['overhead_percentage'] > 10:  # 10% max overhead
        raise PerformanceError(f"Performance regression detected: {overhead['overhead_percentage']:.1%}")

    print("✅ CI validation passed")
    return True
```

---

## 🎯 Testing Best Practices

### 1. Regular Validation

```python
# Run validation after major changes
def post_deployment_validation():
    validator = LineageValidator(tracker)
    results = validator.validate_all()

    # Log results
    logging.info(f"Validation results: {results}")

    # Alert on failures
    if not results['is_valid']:
        send_alert(f"Lineage validation failed: {results['issues']}")
```

### 2. Performance Monitoring

```python
# Monitor performance trends
def monitor_performance_trends():
    benchmark = PerformanceBenchmark(tracker)
    current_results = benchmark.run_comprehensive_benchmark()

    # Compare with historical data
    historical_results = load_historical_benchmarks()
    comparison = benchmark.compare_with_baseline(historical_results)

    # Alert on regressions
    if comparison['regression_detected']:
        send_performance_alert(comparison)
```

### 3. Automated Quality Checks

```python
# Automated quality assurance
def automated_quality_pipeline():
    quality_validator = QualityValidator(tracker)

    # Check coverage requirements
    coverage = quality_validator.calculate_coverage()
    if coverage < 0.8:  # 80% minimum coverage
        raise QualityError(f"Coverage below threshold: {coverage:.1%}")

    # Validate quality rules
    rule_results = quality_validator.validate_quality_rules()
    failed_rules = [rule for rule, result in rule_results.items() if not result['passed']]

    if failed_rules:
        raise QualityError(f"Quality rules failed: {failed_rules}")
```

---

_This comprehensive testing framework ensures your DataLineagePy implementation is accurate, performant, and production-ready!_ 🧪✅
