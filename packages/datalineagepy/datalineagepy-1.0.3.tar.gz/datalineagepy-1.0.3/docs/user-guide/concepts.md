# Core Concepts

Understanding the fundamental concepts behind DataLineagePy will help you use it effectively in your data workflows.

## 🎯 What is Data Lineage?

**Data lineage** is the documentation of data's journey through your pipeline - from source to destination, including all transformations, dependencies, and relationships along the way.

### Why Data Lineage Matters

- **Debugging**: Quickly trace data issues to their source
- **Impact Analysis**: Understand what will break if you change something
- **Compliance**: Document data flow for regulatory requirements
- **Documentation**: Automatically generate pipeline documentation
- **Quality Assurance**: Validate your data transformations

## 🏗️ DataLineagePy Architecture

### Core Components

#### 1. **LineageTracker**

The central hub that manages all lineage information.

```python
from lineagepy import LineageTracker

tracker = LineageTracker()
```

**Key Responsibilities:**

- Store and manage the lineage graph
- Track relationships between data elements
- Provide query and visualization capabilities
- Maintain performance metrics

#### 2. **DataFrameWrapper**

A transparent wrapper around pandas DataFrames that automatically tracks operations.

```python
from lineagepy import DataFrameWrapper

df_wrapped = DataFrameWrapper(df, tracker=tracker, name="sales_data")
```

**Key Features:**

- **Transparent**: Works exactly like a pandas DataFrame
- **Automatic**: Tracks all operations without extra code
- **Lightweight**: Minimal performance overhead
- **Compatible**: Works with all pandas operations

#### 3. **Lineage Graph**

The underlying data structure that stores relationships.

```python
# Graph structure
nodes = {
    'table_nodes': ['customers', 'orders', 'products'],
    'column_nodes': ['customer_id', 'order_amount', 'product_name'],
    'operation_nodes': ['filter', 'join', 'aggregate']
}

edges = [
    ('customers.customer_id', 'join_op', 'customer_orders.customer_id'),
    ('orders.amount', 'sum_op', 'summary.total_amount')
]
```

## 📊 Types of Lineage Tracking

### 1. **Table-Level Lineage**

Tracks relationships between entire DataFrames/tables.

```python
# Table A → Operation → Table B
customers → join → customer_orders
orders → join → customer_orders
customer_orders → aggregate → summary
```

### 2. **Column-Level Lineage** ⭐

Tracks relationships between specific columns (DataLineagePy's specialty).

```python
# Column dependencies
df['total_price'] = df['price'] * df['quantity']
# Creates lineage: price, quantity → total_price

df['profit'] = df['total_price'] - df['cost']
# Creates lineage: total_price, cost → profit
# Indirect lineage: price, quantity → profit (through total_price)
```

### 3. **Operation Lineage**

Tracks the specific transformations applied.

```python
operations = [
    {'type': 'filter', 'condition': 'age > 18'},
    {'type': 'groupby', 'columns': ['category']},
    {'type': 'aggregate', 'function': 'sum'}
]
```

## 🔄 Lineage Tracking Process

### Step 1: Initialization

```python
from lineagepy import LineageTracker, DataFrameWrapper
import pandas as pd

# Create tracker
tracker = LineageTracker()
```

### Step 2: Wrap DataFrames

```python
# Original data
customers = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35]
})

# Wrap for tracking
customers_tracked = DataFrameWrapper(
    customers,
    tracker=tracker,
    name="customers"
)
```

### Step 3: Perform Operations

```python
# Filter operation - automatically tracked
adults = customers_tracked[customers_tracked['age'] >= 18]

# New column - automatically tracked
adults_with_category = adults.assign(
    age_category=adults['age'].apply(lambda x: 'young' if x < 30 else 'adult')
)
```

### Step 4: Query Lineage

```python
# Get column lineage
lineage = tracker.get_column_lineage('age_category')
print(f"age_category depends on: {lineage['source_columns']}")
# Output: age_category depends on: ['age']

# Get operation history
operations = tracker.get_operation_history('age_category')
for op in operations:
    print(f"{op['type']}: {op['description']}")
```

## 🎨 Lineage Visualization

### Graph Representation

DataLineagePy represents lineage as a directed acyclic graph (DAG):

```
[customers.id] ──┐
                 ├─→ [join_op] ──→ [customer_orders.customer_id]
[orders.customer_id] ─┘

[orders.amount] ──→ [sum_op] ──→ [summary.total_amount]
```

### Interactive Visualizations

```python
# Basic visualization
tracker.visualize()

# Advanced visualization
tracker.visualize(
    layout='hierarchical',
    show_column_details=True,
    highlight_path=['customers', 'customer_orders', 'summary']
)

# Generate dashboard
tracker.generate_dashboard('lineage_report.html')
```

## 🔍 Lineage Queries

### Basic Queries

```python
# Get all source columns for a specific column
sources = tracker.get_source_columns('profit')
# Returns: ['price', 'quantity', 'cost']

# Get all derived columns from a source
derived = tracker.get_derived_columns('price')
# Returns: ['total_price', 'profit', 'price_category']

# Get direct dependencies only
direct_deps = tracker.get_direct_dependencies('total_price')
# Returns: ['price', 'quantity']
```

### Advanced Queries

```python
# Get full lineage path
path = tracker.get_lineage_path('customers.id', 'summary.customer_count')
# Returns: ['customers.id', 'join_op', 'customer_orders.customer_id',
#          'groupby_op', 'summary.customer_count']

# Find impact of changes
impact = tracker.get_impact_analysis('price')
# Returns all columns/tables that would be affected if 'price' changes

# Get lineage depth
depth = tracker.get_lineage_depth('final_score')
# Returns: 4 (number of transformation levels)
```

## 📋 Metadata Management

### Column Metadata

```python
# Set column metadata
tracker.set_column_metadata('customer_id', {
    'type': 'integer',
    'description': 'Unique customer identifier',
    'business_rules': ['always positive', 'never null'],
    'data_quality': {'null_rate': 0.0, 'unique_rate': 1.0}
})

# Retrieve metadata
metadata = tracker.get_column_metadata('customer_id')
```

### Operation Metadata

```python
# Track operation details
tracker.track_operation(
    source_columns=['price', 'quantity'],
    target_columns=['total_price'],
    operation_type='calculation',
    operation_details={
        'formula': 'price * quantity',
        'business_logic': 'Calculate total price before tax',
        'validation_rules': ['result must be positive']
    }
)
```

### Quality Metrics

```python
# Track data quality lineage
tracker.add_quality_check(
    column='email',
    check_type='format_validation',
    rule='valid email format',
    pass_rate=0.95
)

# Get quality lineage
quality_lineage = tracker.get_quality_lineage('email')
```

## 🔧 Configuration Options

### Tracking Levels

```python
# Detailed tracking (default)
tracker.set_tracking_level('detailed')
# Tracks: operations, metadata, performance, quality

# Lightweight tracking (for performance)
tracker.set_tracking_level('lightweight')
# Tracks: basic operations only

# Custom tracking
tracker.set_tracking_level('custom', {
    'track_operations': True,
    'track_metadata': False,
    'track_performance': True,
    'track_quality': False
})
```

### Performance Settings

```python
# Enable batch mode for large datasets
tracker.set_batch_mode(True)

# Set memory limits
tracker.set_memory_limit('1GB')

# Configure caching
tracker.enable_caching(cache_size='100MB')
```

## 🎯 Common Patterns

### Pattern 1: ETL Pipeline

```python
# Extract
raw_data = DataFrameWrapper(pd.read_csv('data.csv'), tracker, 'raw_data')

# Transform
cleaned = raw_data.dropna()  # Remove nulls
validated = cleaned[cleaned['amount'] > 0]  # Business rules
enriched = validated.merge(lookup_table, on='key')  # Enrich
aggregated = enriched.groupby('category').agg({'amount': 'sum'})  # Aggregate

# Load
final_result = aggregated.reset_index()
tracker.mark_as_output(final_result, 'final_report')
```

### Pattern 2: Feature Engineering

```python
# Raw features
features = DataFrameWrapper(df, tracker, 'raw_features')

# Derived features
features_eng = features.assign(
    # Numerical transformations
    log_price=np.log(features['price']),
    price_per_unit=features['price'] / features['quantity'],

    # Categorical features
    price_category=pd.cut(features['price'], bins=3, labels=['low', 'med', 'high']),

    # Time features
    day_of_week=features['date'].dt.day_name(),
    is_weekend=features['date'].dt.weekday >= 5
)

# Feature selection
selected = features_eng[['log_price', 'price_category', 'is_weekend', 'target']]
tracker.mark_as_output(selected, 'training_features')
```

### Pattern 3: Data Quality Pipeline

```python
# Input validation
validated = raw_data[
    (raw_data['age'] >= 0) &
    (raw_data['age'] <= 120) &
    (raw_data['email'].str.contains('@'))
]

# Completeness checks
complete = validated.dropna(subset=['required_field1', 'required_field2'])

# Consistency checks
consistent = complete[complete['start_date'] <= complete['end_date']]

# Track quality rules
tracker.add_quality_rule('age_range', 'age between 0 and 120')
tracker.add_quality_rule('email_format', 'email contains @')
tracker.add_quality_rule('date_consistency', 'start_date <= end_date')
```

## 🚨 Best Practices

### 1. **Naming Conventions**

```python
# Good: Descriptive names
customers_raw = DataFrameWrapper(df, tracker, 'customers_raw')
customers_cleaned = clean_data(customers_raw)
customers_enriched = enrich_data(customers_cleaned)

# Bad: Generic names
df1 = DataFrameWrapper(df, tracker, 'df1')
df2 = process(df1)
```

### 2. **Operation Documentation**

```python
# Good: Document business logic
tracker.track_operation(
    source_columns=['revenue', 'costs'],
    target_columns=['profit'],
    operation_type='business_calculation',
    description='Calculate profit as revenue minus costs for financial reporting'
)

# Good: Include validation rules
tracker.add_validation_rule('profit', 'must be numeric and can be negative')
```

### 3. **Quality Checkpoints**

```python
# Add quality checkpoints at key stages
def validate_data_quality(df_wrapped, stage_name):
    validator = QualityValidator(tracker)
    results = validator.validate_stage(df_wrapped, stage_name)

    if not results['passed']:
        raise ValueError(f"Quality check failed at {stage_name}: {results['issues']}")

    return df_wrapped

# Use throughout pipeline
customers_cleaned = validate_data_quality(customers_raw, 'raw_data_validation')
```

### 4. **Performance Monitoring**

```python
# Monitor performance at each stage
with tracker.performance_monitor('data_cleaning'):
    cleaned_data = clean_data(raw_data)

with tracker.performance_monitor('feature_engineering'):
    features = engineer_features(cleaned_data)
```

## 🎓 Understanding Lineage Complexity

### Simple Lineage

```python
df['total'] = df['price'] * df['quantity']
# Lineage: price, quantity → total (direct dependency)
```

### Complex Lineage

```python
# Multi-step transformation
df['adjusted_price'] = df['price'] * df['adjustment_factor']
df['total'] = df['adjusted_price'] * df['quantity']
df['profit'] = df['total'] - df['cost']

# Lineage graph:
# price, adjustment_factor → adjusted_price
# adjusted_price, quantity → total
# total, cost → profit
# Indirect: price, adjustment_factor, quantity, cost → profit
```

### Cross-DataFrame Lineage

```python
# Join creates cross-DataFrame dependencies
result = customers.merge(orders, on='customer_id')
# Lineage: customers.*, orders.* → result.*

summary = result.groupby('customer_name')['amount'].sum()
# Lineage: customers.customer_name, orders.amount → summary
```

---

## 🎯 Next Steps

Now that you understand the core concepts:

1. **[DataFrameWrapper Guide](dataframe-wrapper.md)** - Learn the wrapper in detail
2. **[LineageTracker Guide](lineage-tracker.md)** - Master the tracker capabilities
3. **[Visualizations Guide](visualizations.md)** - Create beautiful lineage charts
4. **[API Reference](../api/core.md)** - Detailed function documentation

_Ready to track some lineage? Check out our [Quick Start Tutorial](../quickstart.md)!_ 🚀
