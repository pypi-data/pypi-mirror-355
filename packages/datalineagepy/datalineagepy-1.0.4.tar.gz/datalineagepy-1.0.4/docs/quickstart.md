# Quick Start Tutorial

Get up and running with DataLineagePy in 30 seconds! This tutorial will show you how to track your first data lineage.

## 🚀 30-Second Setup

### Step 1: Install DataLineagePy

```bash
pip install lineagepy
```

### Step 2: Import and Initialize

```python
from lineagepy import LineageTracker, DataFrameWrapper
import pandas as pd

# Create a lineage tracker
tracker = LineageTracker()
```

### Step 3: Track Your First Lineage

```python
# Create some sample data
df = pd.DataFrame({
    'product': ['Laptop', 'Phone', 'Tablet'],
    'price': [1000, 500, 300],
    'quantity': [10, 20, 15]
})

# Wrap the DataFrame for lineage tracking
df_wrapped = DataFrameWrapper(df, tracker=tracker, name="sales_data")

# Perform operations - lineage is tracked automatically!
revenue = df_wrapped.assign(revenue=df_wrapped['price'] * df_wrapped['quantity'])
high_value = revenue[revenue['revenue'] > 5000]

# Visualize the lineage
tracker.visualize()
```

**Congratulations!** 🎉 You just tracked your first data lineage!

## 📊 What Just Happened?

DataLineagePy automatically tracked:

1. **Input Data**: `sales_data` DataFrame with columns `product`, `price`, `quantity`
2. **Transformation**: Created `revenue` column from `price × quantity`
3. **Filter Operation**: Selected rows where `revenue > 5000`
4. **Column Dependencies**: `revenue` depends on `price` and `quantity`

## 🔍 Exploring Your Lineage

### View Lineage Information

```python
# Get lineage for a specific column
lineage_info = tracker.get_column_lineage('revenue')
print(f"Revenue column depends on: {lineage_info['dependencies']}")

# Get all operations performed
operations = tracker.get_all_operations()
print(f"Total operations tracked: {len(operations)}")

# Show graph statistics
stats = tracker.get_graph_stats()
print(f"Nodes: {stats['nodes']}, Edges: {stats['edges']}")
```

### Generate Reports

```python
# Create HTML dashboard
tracker.generate_dashboard("my_first_lineage.html")
print("Dashboard saved to my_first_lineage.html")

# Export lineage data
lineage_data = tracker.export_lineage()
print("Lineage data exported successfully")
```

## 📈 More Realistic Example

Let's try a more complex data pipeline:

```python
import pandas as pd
from lineagepy import LineageTracker, DataFrameWrapper

# Initialize tracker
tracker = LineageTracker()

# Create realistic datasets
customers = pd.DataFrame({
    'customer_id': [1, 2, 3, 4, 5],
    'customer_name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
    'age': [25, 30, 35, 28, 42],
    'country': ['USA', 'UK', 'Canada', 'USA', 'Germany']
})

orders = pd.DataFrame({
    'order_id': [101, 102, 103, 104, 105],
    'customer_id': [1, 2, 1, 3, 2],
    'product': ['Laptop', 'Phone', 'Tablet', 'Laptop', 'Phone'],
    'amount': [1200, 800, 400, 1200, 800],
    'order_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19']
})

# Wrap DataFrames
customers_wrapped = DataFrameWrapper(customers, tracker=tracker, name="customers")
orders_wrapped = DataFrameWrapper(orders, tracker=tracker, name="orders")

# Perform complex transformations
# 1. Add age groups
customers_segmented = customers_wrapped.assign(
    age_group=customers_wrapped['age'].apply(lambda x: 'Young' if x < 30 else 'Adult')
)

# 2. Join customers with orders
customer_orders = customers_segmented.merge(
    orders_wrapped,
    on='customer_id',
    how='inner'
)

# 3. Calculate metrics
summary = customer_orders.groupby(['country', 'age_group']).agg({
    'amount': ['sum', 'mean', 'count']
}).reset_index()

# 4. Filter high-value segments
high_value_segments = summary[summary[('amount', 'sum')] > 1000]

print("✅ Complex pipeline completed!")
print(f"📊 Tracked {len(tracker.get_all_operations())} operations")
```

### Visualize Complex Lineage

```python
# Generate detailed dashboard
tracker.generate_dashboard("complex_pipeline.html", include_details=True)

# Show column-level lineage for a specific result
column_lineage = tracker.get_column_lineage(('amount', 'sum'))
print(f"Sum amount depends on: {column_lineage}")

# Display graph
tracker.visualize(layout='hierarchical', show_column_details=True)
```

## 🧪 Quality Assurance

DataLineagePy includes built-in testing capabilities:

```python
from lineagepy.testing import LineageValidator, QualityValidator

# Validate lineage integrity
validator = LineageValidator(tracker)
validation_results = validator.validate_all()

if validation_results['is_valid']:
    print("✅ Lineage is valid!")
else:
    print("❌ Lineage issues found:")
    for issue in validation_results['issues']:
        print(f"  - {issue}")

# Check data quality metrics
quality = QualityValidator(tracker)
coverage = quality.calculate_coverage()
completeness = quality.check_completeness()

print(f"📊 Lineage coverage: {coverage:.1%}")
print(f"📋 Completeness score: {completeness:.1%}")
```

## 📊 Performance Monitoring

Track performance as you work:

```python
from lineagepy.testing import PerformanceBenchmark

# Create benchmark
benchmark = PerformanceBenchmark(tracker)

# Run performance tests
results = benchmark.benchmark_operations()
print(f"⚡ Average operation time: {results['avg_time']:.2f}ms")
print(f"💾 Memory usage: {results['memory_mb']:.1f}MB")

# Generate performance report
benchmark.generate_report("performance_report.html")
```

## 🎯 Common Patterns

### Pattern 1: ETL Pipeline

```python
# Extract
raw_data = DataFrameWrapper(pd.read_csv('data.csv'), tracker, 'raw_data')

# Transform
cleaned = raw_data.dropna()
enriched = cleaned.merge(lookup_table, on='key')
aggregated = enriched.groupby('category').sum()

# Load (track final output)
final_result = aggregated.reset_index()
tracker.mark_output(final_result, 'final_report')
```

### Pattern 2: ML Feature Engineering

```python
# Raw features
features = DataFrameWrapper(df, tracker, 'raw_features')

# Feature engineering
normalized = features.assign(
    price_normalized=(features['price'] - features['price'].mean()) / features['price'].std()
)

# Feature selection
selected_features = normalized[['price_normalized', 'category', 'target']]

# Track ML training data
tracker.mark_output(selected_features, 'ml_training_data')
```

### Pattern 3: Data Quality Checks

```python
# Input validation
validated = raw_data[raw_data['amount'] > 0]  # Remove negative amounts
cleaned = validated.dropna(subset=['required_field'])

# Business rules
business_valid = cleaned[
    (cleaned['date'] >= '2024-01-01') &
    (cleaned['status'].isin(['active', 'pending']))
]

# Track data quality lineage
tracker.add_quality_check('positive_amounts', 'amount > 0')
tracker.add_quality_check('required_fields', 'no nulls in required_field')
```

## 🎨 Visualization Options

### Basic Visualization

```python
# Simple graph view
tracker.visualize()
```

### Customized Visualization

```python
# Advanced visualization options
tracker.visualize(
    layout='hierarchical',           # or 'force', 'circular'
    show_column_details=True,        # Show column-level lineage
    highlight_critical_path=True,    # Highlight main data flow
    color_by_operation_type=True,    # Color code by operation
    save_path='lineage_graph.png'    # Save to file
)
```

### Interactive Dashboard

```python
# Full-featured dashboard
tracker.generate_dashboard(
    output_file='dashboard.html',
    include_performance_metrics=True,
    include_data_quality_summary=True,
    include_interactive_filters=True
)
```

## ⚡ Performance Tips

### For Large Datasets

```python
# Use batch tracking for better performance
tracker.set_batch_mode(True)

# Process in chunks
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    chunk_wrapped = DataFrameWrapper(chunk, tracker, f'chunk_{i}')
    # Process chunk...

# Finalize batch
tracker.finalize_batch()
```

### Memory Optimization

```python
# Enable memory optimization
tracker.enable_memory_optimization()

# Clear intermediate results
tracker.clear_intermediate_nodes()

# Use lightweight tracking
tracker.set_tracking_level('lightweight')  # vs 'detailed'
```

## 🆘 Common Issues & Solutions

### Issue 1: "Module not found"

```python
# Solution: Check installation
import sys
print(sys.path)
# Reinstall if needed: pip install --upgrade lineagepy
```

### Issue 2: Performance slow with large data

```python
# Solution: Enable batch mode
tracker.set_batch_mode(True)
tracker.set_tracking_level('lightweight')
```

### Issue 3: Complex graphs hard to read

```python
# Solution: Use hierarchical layout and filters
tracker.visualize(
    layout='hierarchical',
    max_nodes_displayed=50,
    filter_by_importance=True
)
```

## 🎯 Next Steps

Now that you've mastered the basics:

1. **[Learn Core Concepts](user-guide/concepts.md)** - Understand lineage fundamentals
2. **[Explore Advanced Features](advanced/testing.md)** - Quality assurance and monitoring
3. **[Check API Reference](api/core.md)** - Detailed function documentation
4. **[See Real Examples](examples/basic.md)** - Industry-specific use cases

## 💡 Pro Tips

1. **Always name your DataFrames** - Makes lineage graphs much clearer
2. **Use descriptive operation names** - Helps with debugging later
3. **Enable validation early** - Catch lineage issues before they become problems
4. **Export dashboards regularly** - Great for documentation and reviews

---

**Congratulations! 🎉** You're now ready to track lineage in your own projects.

**Questions?** Check our [FAQ](faq.md) or [create an issue](https://github.com/yourusername/DataLineagePy/issues).

_Happy lineage tracking!_ 📊✨
