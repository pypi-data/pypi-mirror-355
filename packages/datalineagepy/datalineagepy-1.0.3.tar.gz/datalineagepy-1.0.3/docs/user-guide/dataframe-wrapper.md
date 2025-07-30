# DataFrameWrapper Complete Guide

The `DataFrameWrapper` is the heart of DataLineagePy - it transparently wraps pandas DataFrames to automatically track lineage for all operations.

## 🎯 Overview

The `DataFrameWrapper` acts as a proxy to pandas DataFrames, intercepting operations to track lineage while maintaining 100% compatibility with pandas syntax.

```python
from lineagepy import LineageTracker, DataFrameWrapper
import pandas as pd

tracker = LineageTracker()
df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})
df_wrapped = DataFrameWrapper(df, tracker=tracker, name="users")

# Use exactly like pandas DataFrame
result = df_wrapped[df_wrapped['age'] > 25]  # Lineage tracked automatically!
```

## 🏗️ Constructor

### `DataFrameWrapper(dataframe, tracker, name, metadata=None)`

Creates a lineage-tracked wrapper around a pandas DataFrame.

**Parameters:**

- `dataframe` (pd.DataFrame): The pandas DataFrame to wrap
- `tracker` (LineageTracker): The lineage tracker instance
- `name` (str): Unique name for this DataFrame in the lineage graph
- `metadata` (dict, optional): Additional metadata to associate

**Example:**

```python
# Basic usage
df_wrapped = DataFrameWrapper(df, tracker, "sales_data")

# With metadata
df_wrapped = DataFrameWrapper(df, tracker, "customers", metadata={
    'source': 'database',
    'table': 'customers',
    'schema': 'public',
    'last_updated': '2024-01-15',
    'owner': 'data_team'
})
```

## 📊 Core Operations

### Selection Operations

#### Column Selection

```python
# Single column
name_col = df_wrapped['name']
# Lineage: users.name → result

# Multiple columns
subset = df_wrapped[['name', 'age']]
# Lineage: users.name, users.age → result

# Column with condition
adults = df_wrapped[df_wrapped['age'] >= 18]
# Lineage: users.age → filter condition, users.* → result
```

#### Row Selection

```python
# Boolean indexing
filtered = df_wrapped[df_wrapped['score'] > 80]
# Lineage: users.score → filter, users.* → result

# iloc selection
first_10 = df_wrapped.iloc[:10]
# Lineage: users.* → result (first 10 rows)

# loc selection
specific = df_wrapped.loc[df_wrapped['status'] == 'active']
# Lineage: users.status → filter, users.* → result
```

#### Query Method

```python
# Using query method
high_scorers = df_wrapped.query('score > 90 and age < 30')
# Lineage: users.score, users.age → filter, users.* → result

# Complex queries
complex_filter = df_wrapped.query('category in ["A", "B"] and value > @threshold')
# Lineage: users.category, users.value → filter, users.* → result
```

### Transformation Operations

#### Adding/Modifying Columns

```python
# Simple assignment
df_wrapped['full_name'] = df_wrapped['first_name'] + ' ' + df_wrapped['last_name']
# Lineage: first_name, last_name → full_name

# Using assign()
enhanced = df_wrapped.assign(
    age_group=df_wrapped['age'] // 10,
    is_adult=df_wrapped['age'] >= 18,
    score_normalized=df_wrapped['score'] / 100
)
# Lineage: age → age_group, age → is_adult, score → score_normalized

# Conditional assignment
df_wrapped['category'] = df_wrapped['score'].apply(
    lambda x: 'High' if x > 80 else 'Medium' if x > 60 else 'Low'
)
# Lineage: score → category
```

#### Mathematical Operations

```python
# Arithmetic operations
df_wrapped['total'] = df_wrapped['price'] * df_wrapped['quantity']
# Lineage: price, quantity → total

df_wrapped['profit'] = df_wrapped['revenue'] - df_wrapped['cost']
# Lineage: revenue, cost → profit

# Multiple operations
df_wrapped['roi'] = (df_wrapped['profit'] / df_wrapped['investment']) * 100
# Lineage: profit, investment → roi
# Indirect: revenue, cost, investment → roi
```

#### String Operations

```python
# String methods
df_wrapped['name_upper'] = df_wrapped['name'].str.upper()
# Lineage: name → name_upper

df_wrapped['email_domain'] = df_wrapped['email'].str.split('@').str[1]
# Lineage: email → email_domain

# String concatenation
df_wrapped['address'] = (df_wrapped['street'] + ', ' +
                        df_wrapped['city'] + ', ' +
                        df_wrapped['state'])
# Lineage: street, city, state → address
```

#### Date/Time Operations

```python
# Date parsing
df_wrapped['date_parsed'] = pd.to_datetime(df_wrapped['date_string'])
# Lineage: date_string → date_parsed

# Date components
df_wrapped['year'] = df_wrapped['date'].dt.year
df_wrapped['month'] = df_wrapped['date'].dt.month
df_wrapped['day_of_week'] = df_wrapped['date'].dt.day_name()
# Lineage: date → year, date → month, date → day_of_week

# Date calculations
df_wrapped['days_since'] = (pd.Timestamp.now() - df_wrapped['date']).dt.days
# Lineage: date → days_since
```

## 🔗 Join Operations

### Merge Operations

```python
# Inner join
customers = DataFrameWrapper(customers_df, tracker, "customers")
orders = DataFrameWrapper(orders_df, tracker, "orders")

customer_orders = customers.merge(orders, on='customer_id', how='inner')
# Lineage: customers.*, orders.* → customer_orders.*
# Join condition: customers.customer_id, orders.customer_id → join

# Left join with suffixes
detailed = customers.merge(orders, on='customer_id', how='left',
                          suffixes=('_cust', '_ord'))
# Lineage tracks suffix mapping: customers.id → detailed.id_cust

# Multiple key join
complex_join = df1.merge(df2, on=['key1', 'key2'], how='outer')
# Lineage: df1.key1, df1.key2, df2.key1, df2.key2 → join condition
```

### Join with Different Column Names

```python
# Join on differently named columns
result = customers.merge(orders, left_on='id', right_on='customer_id')
# Lineage: customers.id, orders.customer_id → join condition

# Multiple column mapping
multi_join = df1.merge(df2,
                      left_on=['id', 'type'],
                      right_on=['user_id', 'category'])
# Lineage tracks all column mappings
```

### Concatenation

```python
# Vertical concatenation
combined = pd.concat([df_wrapped1, df_wrapped2], ignore_index=True)
# Lineage: df1.*, df2.* → combined.*

# Horizontal concatenation
side_by_side = pd.concat([df_wrapped1, df_wrapped2], axis=1)
# Lineage: df1.*, df2.* → side_by_side.*
```

## 📈 Aggregation Operations

### GroupBy Operations

```python
# Simple groupby
grouped = df_wrapped.groupby('category')['amount'].sum()
# Lineage: category → grouping key, amount → sum(amount)

# Multiple aggregations
agg_result = df_wrapped.groupby('category').agg({
    'amount': ['sum', 'mean', 'count'],
    'quantity': 'max',
    'price': 'min'
})
# Lineage: category → grouping, amount → sum/mean/count,
#          quantity → max, price → min

# Custom aggregations
custom_agg = df_wrapped.groupby(['region', 'category']).apply(
    lambda x: x['sales'].sum() / x['visits'].sum()
)
# Lineage: region, category → grouping, sales, visits → custom calculation
```

### Pivot Operations

```python
# Pivot table
pivot = df_wrapped.pivot_table(
    values='amount',
    index='category',
    columns='month',
    aggfunc='sum'
)
# Lineage: category → index, month → columns, amount → values

# Pivot with multiple values
multi_pivot = df_wrapped.pivot_table(
    values=['amount', 'quantity'],
    index='category',
    columns='region',
    aggfunc={'amount': 'sum', 'quantity': 'mean'}
)
# Lineage tracks each value-function combination
```

### Rolling/Window Operations

```python
# Rolling averages
df_wrapped['rolling_avg'] = df_wrapped['price'].rolling(window=3).mean()
# Lineage: price → rolling_avg (with window context)

# Expanding operations
df_wrapped['cumulative_sum'] = df_wrapped['amount'].expanding().sum()
# Lineage: amount → cumulative_sum

# Custom window functions
df_wrapped['custom_window'] = df_wrapped.rolling(window=5).apply(
    lambda x: x.max() - x.min()
)
# Lineage: all columns → custom_window (custom function)
```

## 🧹 Data Cleaning Operations

### Handling Missing Values

```python
# Drop missing values
cleaned = df_wrapped.dropna()
# Lineage: df.* → cleaned.* (with null removal metadata)

# Fill missing values
filled = df_wrapped.fillna({
    'age': df_wrapped['age'].mean(),
    'category': 'Unknown',
    'score': 0
})
# Lineage: age → filled.age (mean imputation),
#          category → filled.category (constant fill)

# Forward/backward fill
ffilled = df_wrapped.fillna(method='ffill')
# Lineage: df.* → ffilled.* (forward fill logic)
```

### Duplicate Handling

```python
# Remove duplicates
unique_rows = df_wrapped.drop_duplicates()
# Lineage: df.* → unique_rows.* (duplicate removal)

# Remove duplicates on specific columns
unique_customers = df_wrapped.drop_duplicates(subset=['customer_id'])
# Lineage: customer_id → deduplication key, df.* → result

# Keep specific duplicate
last_entry = df_wrapped.drop_duplicates(subset=['id'], keep='last')
# Lineage tracks keep strategy
```

### Data Type Conversions

```python
# Type conversions
df_wrapped['age'] = df_wrapped['age'].astype(int)
# Lineage: original_age → age (int conversion)

df_wrapped['date'] = pd.to_datetime(df_wrapped['date_string'])
# Lineage: date_string → date (datetime conversion)

# Category conversion
df_wrapped['category'] = df_wrapped['category'].astype('category')
# Lineage: original_category → category (categorical conversion)
```

## 🔧 Advanced Operations

### Apply Functions

```python
# Apply to series
df_wrapped['processed'] = df_wrapped['text'].apply(process_text)
# Lineage: text → processed (custom function: process_text)

# Apply to DataFrame
df_wrapped['combined'] = df_wrapped.apply(
    lambda row: combine_values(row['col1'], row['col2']), axis=1
)
# Lineage: col1, col2 → combined (custom function: combine_values)

# Apply with multiple columns
df_wrapped[['new_col1', 'new_col2']] = df_wrapped.apply(
    lambda row: multi_output_function(row), axis=1, result_type='expand'
)
# Lineage: df.* → new_col1, new_col2 (multi-output function)
```

### Transform Operations

```python
# Group transform
df_wrapped['group_mean'] = df_wrapped.groupby('category')['value'].transform('mean')
# Lineage: category → grouping, value → group_mean (mean transform)

# Custom transform
df_wrapped['normalized'] = df_wrapped.groupby('category')['score'].transform(
    lambda x: (x - x.mean()) / x.std()
)
# Lineage: category → grouping, score → normalized (z-score)
```

### Resampling (Time Series)

```python
# Time-based resampling
monthly = df_wrapped.set_index('date').resample('M').sum()
# Lineage: date → index, df.* → monthly.* (monthly aggregation)

# Custom resampling
custom_resample = df_wrapped.resample('D', on='timestamp').agg({
    'sales': 'sum',
    'visits': 'count',
    'revenue': 'mean'
})
# Lineage: timestamp → resampling key, sales/visits/revenue → aggregated values
```

## 📋 Property Access

### DataFrame Properties

```python
# Shape information (doesn't create lineage)
rows, cols = df_wrapped.shape
print(f"DataFrame has {rows} rows and {cols} columns")

# Column information
columns = df_wrapped.columns.tolist()
dtypes = df_wrapped.dtypes.to_dict()

# Index information
index_name = df_wrapped.index.name
```

### Statistical Operations

```python
# Descriptive statistics (creates lineage to summary stats)
stats = df_wrapped.describe()
# Lineage: df.numeric_columns → stats.*

# Correlation matrix
corr = df_wrapped.corr()
# Lineage: df.numeric_columns → correlation_matrix

# Custom statistics
df_wrapped['z_score'] = (df_wrapped['value'] - df_wrapped['value'].mean()) / df_wrapped['value'].std()
# Lineage: value → z_score (standardization)
```

## 🎯 Lineage-Specific Methods

### Lineage Queries

```python
# Get lineage for specific column
lineage = df_wrapped.get_column_lineage('total_price')
print(f"total_price depends on: {lineage['source_columns']}")

# Get operation history
operations = df_wrapped.get_operation_history()
for op in operations:
    print(f"{op['timestamp']}: {op['operation']}")

# Get metadata
metadata = df_wrapped.get_metadata()
print(f"Source: {metadata.get('source', 'unknown')}")
```

### Manual Lineage Tracking

```python
# Track custom operation
df_wrapped.track_custom_operation(
    source_columns=['col1', 'col2'],
    target_columns=['result'],
    operation_type='business_logic',
    description='Calculate business metric'
)

# Add quality metadata
df_wrapped.add_quality_check('email', 'format_validation', pass_rate=0.95)

# Mark as output
df_wrapped.mark_as_output('final_report')
```

## 🔍 Inspection and Debugging

### Lineage Visualization

```python
# Visualize lineage for this DataFrame
df_wrapped.visualize_lineage()

# Show column dependencies
df_wrapped.show_column_dependencies('target_column')

# Export lineage
df_wrapped.export_lineage('output.json')
```

### Performance Monitoring

```python
# Check tracking overhead
performance = df_wrapped.get_performance_metrics()
print(f"Tracking overhead: {performance['overhead_ms']}ms")

# Memory usage
memory_info = df_wrapped.get_memory_usage()
print(f"Memory usage: {memory_info['total_mb']}MB")
```

## ⚠️ Common Pitfalls and Solutions

### Pitfall 1: Losing Wrapper

```python
# WRONG - loses lineage tracking
df_unwrapped = df_wrapped.to_pandas()  # Becomes regular DataFrame
result = df_unwrapped['col1'] * 2  # No lineage tracked

# CORRECT - maintains tracking
result = df_wrapped['col1'] * 2  # Lineage tracked
```

### Pitfall 2: External Function Calls

```python
# WRONG - external functions don't track lineage
external_result = external_function(df_wrapped.to_pandas())

# CORRECT - register or wrap external functions
@register_lineage_function(inputs=['input_cols'], outputs=['output_cols'])
def external_function(df):
    # Your logic here
    return processed_df

result = external_function(df_wrapped)
```

### Pitfall 3: In-place Operations

```python
# WRONG - in-place operations can break tracking
df_wrapped.drop('col1', axis=1, inplace=True)  # May lose references

# CORRECT - use assignment
df_wrapped = df_wrapped.drop('col1', axis=1)  # Maintains tracking
```

## 🚀 Performance Optimization

### Batch Operations

```python
# For large datasets, use batch mode
tracker.set_batch_mode(True)

# Process in chunks
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    chunk_wrapped = DataFrameWrapper(chunk, tracker, f'chunk_{i}')
    # Process chunk

tracker.finalize_batch()
```

### Memory Management

```python
# Clear intermediate results
tracker.clear_intermediate_nodes()

# Use lightweight tracking for large pipelines
tracker.set_tracking_level('lightweight')

# Checkpoint progress
tracker.checkpoint('stage_1_complete')
```

## 📚 Integration Examples

### With Scikit-learn

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Feature preparation with lineage
features = df_wrapped[['feature1', 'feature2', 'feature3']]
target = df_wrapped['target']

# Split data (lineage tracked)
X_train, X_test, y_train, y_test = train_test_split(
    features.to_pandas(), target.to_pandas(), test_size=0.2
)

# Track ML pipeline
tracker.track_ml_split(features, target, test_size=0.2)
```

### With Database Connections

```python
# Reading from database with lineage
import sqlalchemy as sa

engine = sa.create_engine('postgresql://...')
query = "SELECT * FROM customers WHERE active = true"

db_data = pd.read_sql(query, engine)
db_wrapped = DataFrameWrapper(db_data, tracker, 'customers_active', metadata={
    'source': 'postgresql',
    'query': query,
    'table': 'customers'
})
```

### With File I/O

```python
# Reading files with lineage
file_data = pd.read_csv('data.csv')
df_wrapped = DataFrameWrapper(file_data, tracker, 'raw_data', metadata={
    'source_file': 'data.csv',
    'file_size': os.path.getsize('data.csv'),
    'load_time': datetime.now()
})

# Saving with lineage export
df_wrapped.to_csv('output.csv')
tracker.export_lineage('lineage.json')
```

---

## 🎯 Next Steps

- **[LineageTracker Guide](lineage-tracker.md)** - Master the central tracker
- **[Visualizations Guide](visualizations.md)** - Create beautiful lineage charts
- **[API Reference](../api/core.md)** - Complete function documentation
- **[Advanced Features](../advanced/testing.md)** - Quality assurance and testing

_Master the DataFrameWrapper and unlock the full power of automatic lineage tracking!_ 🚀
