# Core API Reference

Complete reference for all DataLineagePy core classes and functions.

## 📚 Table of Contents

- [LineageTracker](#lineagetracker)
- [DataFrameWrapper](#dataframewrapper)
- [LineageNode](#lineagenode)
- [LineageEdge](#lineageedge)
- [Utility Functions](#utility-functions)

---

## LineageTracker

The central class that manages all lineage information and provides query capabilities.

### Constructor

#### `LineageTracker(config=None)`

Creates a new lineage tracker instance.

**Parameters:**

- `config` (dict, optional): Configuration options for the tracker

**Configuration Options:**

```python
config = {
    'tracking_level': 'detailed',  # 'detailed', 'lightweight', 'custom'
    'enable_performance_tracking': True,
    'enable_quality_tracking': True,
    'max_nodes': 50000,
    'memory_limit': '1GB',
    'batch_mode': False
}
```

**Example:**

```python
# Basic tracker
tracker = LineageTracker()

# Configured tracker
tracker = LineageTracker(config={
    'tracking_level': 'lightweight',
    'max_nodes': 10000
})
```

### Core Methods

#### `track_operation(source_columns, target_columns, operation_type, **kwargs)`

Manually track an operation between columns.

**Parameters:**

- `source_columns` (list): List of source column names
- `target_columns` (list): List of target column names
- `operation_type` (str): Type of operation ('filter', 'transform', 'aggregate', etc.)
- `**kwargs`: Additional operation metadata

**Returns:**

- `str`: Operation ID

**Example:**

```python
op_id = tracker.track_operation(
    source_columns=['price', 'quantity'],
    target_columns=['total'],
    operation_type='calculation',
    formula='price * quantity',
    business_logic='Calculate total before tax'
)
```

#### `get_column_lineage(column_name, table_name=None)`

Get complete lineage for a specific column.

**Parameters:**

- `column_name` (str): Name of the column
- `table_name` (str, optional): Name of the table/DataFrame

**Returns:**

- `dict`: Lineage information containing:
  - `source_columns` (list): Direct source columns
  - `all_sources` (list): All transitive sources
  - `operations` (list): Operations in lineage path
  - `depth` (int): Lineage depth
  - `dependencies` (dict): Detailed dependency graph

**Example:**

```python
lineage = tracker.get_column_lineage('profit')
print(f"Sources: {lineage['source_columns']}")
print(f"Depth: {lineage['depth']}")
```

#### `get_source_columns(column_name, table_name=None)`

Get all source columns for a given column.

**Parameters:**

- `column_name` (str): Target column name
- `table_name` (str, optional): Table name

**Returns:**

- `list`: List of source column names

**Example:**

```python
sources = tracker.get_source_columns('final_score')
# Returns: ['base_score', 'bonus', 'penalty']
```

#### `get_derived_columns(column_name, table_name=None)`

Get all columns derived from a given source column.

**Parameters:**

- `column_name` (str): Source column name
- `table_name` (str, optional): Table name

**Returns:**

- `list`: List of derived column names

**Example:**

```python
derived = tracker.get_derived_columns('price')
# Returns: ['total_price', 'profit', 'price_category']
```

#### `get_lineage_path(source_column, target_column)`

Get the lineage path between two columns.

**Parameters:**

- `source_column` (str): Starting column
- `target_column` (str): Ending column

**Returns:**

- `list`: Ordered list of nodes in the path

**Example:**

```python
path = tracker.get_lineage_path('raw_price', 'final_profit')
# Returns: ['raw_price', 'clean_price', 'total_price', 'profit', 'final_profit']
```

#### `get_impact_analysis(column_name, table_name=None)`

Analyze the impact of changing a specific column.

**Parameters:**

- `column_name` (str): Column to analyze
- `table_name` (str, optional): Table name

**Returns:**

- `dict`: Impact analysis containing:
  - `directly_affected` (list): Immediately dependent columns
  - `transitively_affected` (list): All affected columns
  - `affected_operations` (list): Operations that would be impacted
  - `risk_level` (str): 'low', 'medium', 'high'

**Example:**

```python
impact = tracker.get_impact_analysis('customer_id')
print(f"Risk level: {impact['risk_level']}")
print(f"Affected columns: {impact['transitively_affected']}")
```

### Graph Operations

#### `get_graph_stats()`

Get statistics about the lineage graph.

**Returns:**

- `dict`: Graph statistics containing:
  - `nodes` (int): Total number of nodes
  - `edges` (int): Total number of edges
  - `tables` (int): Number of table nodes
  - `columns` (int): Number of column nodes
  - `operations` (int): Number of operation nodes
  - `max_depth` (int): Maximum lineage depth
  - `complexity_score` (float): Graph complexity metric

**Example:**

```python
stats = tracker.get_graph_stats()
print(f"Graph has {stats['nodes']} nodes and {stats['edges']} edges")
```

#### `get_all_operations()`

Get all tracked operations.

**Returns:**

- `list`: List of operation dictionaries

**Example:**

```python
operations = tracker.get_all_operations()
for op in operations:
    print(f"{op['timestamp']}: {op['type']} - {op['description']}")
```

#### `clear_graph()`

Clear all lineage information.

**Example:**

```python
tracker.clear_graph()
```

#### `merge_tracker(other_tracker)`

Merge lineage from another tracker.

**Parameters:**

- `other_tracker` (LineageTracker): Tracker to merge from

**Example:**

```python
tracker.merge_tracker(other_tracker)
```

### Visualization Methods

#### `visualize(layout='force', **kwargs)`

Generate an interactive visualization of the lineage graph.

**Parameters:**

- `layout` (str): Layout algorithm ('force', 'hierarchical', 'circular')
- `**kwargs`: Visualization options

**Visualization Options:**

```python
kwargs = {
    'show_column_details': True,
    'color_by_operation_type': True,
    'highlight_path': ['source', 'target'],
    'max_nodes_displayed': 100,
    'filter_by_importance': True,
    'save_path': 'lineage.png',
    'width': 1200,
    'height': 800
}
```

**Example:**

```python
tracker.visualize(
    layout='hierarchical',
    show_column_details=True,
    save_path='lineage_graph.png'
)
```

#### `generate_dashboard(output_file, **options)`

Generate an interactive HTML dashboard.

**Parameters:**

- `output_file` (str): Path to save HTML file
- `**options`: Dashboard configuration options

**Dashboard Options:**

```python
options = {
    'include_performance_metrics': True,
    'include_data_quality_summary': True,
    'include_interactive_filters': True,
    'theme': 'light',  # 'light', 'dark'
    'title': 'Data Lineage Dashboard'
}
```

**Example:**

```python
tracker.generate_dashboard(
    'dashboard.html',
    include_performance_metrics=True,
    theme='dark'
)
```

### Export/Import Methods

#### `export_lineage(format='json', output_path=None)`

Export lineage information in various formats.

**Parameters:**

- `format` (str): Export format ('json', 'csv', 'graphviz', 'yaml')
- `output_path` (str, optional): Path to save file

**Returns:**

- `str` or `dict`: Exported lineage data

**Example:**

```python
# Export to JSON
lineage_json = tracker.export_lineage('json', 'lineage.json')

# Export to Graphviz DOT format
tracker.export_lineage('graphviz', 'lineage.dot')
```

#### `import_lineage(data, format='json')`

Import lineage information.

**Parameters:**

- `data` (str or dict): Lineage data to import
- `format` (str): Import format

**Example:**

```python
with open('lineage.json', 'r') as f:
    lineage_data = json.load(f)
tracker.import_lineage(lineage_data, 'json')
```

### Quality and Validation Methods

#### `add_quality_check(column_name, check_type, rule, **metadata)`

Add a data quality check to lineage.

**Parameters:**

- `column_name` (str): Column being validated
- `check_type` (str): Type of check ('format', 'range', 'uniqueness', etc.)
- `rule` (str): Description of the validation rule
- `**metadata`: Additional quality metadata

**Example:**

```python
tracker.add_quality_check(
    'email',
    'format_validation',
    'valid email format',
    regex=r'^[^@]+@[^@]+\.[^@]+$',
    pass_rate=0.95
)
```

#### `get_quality_lineage(column_name)`

Get quality-related lineage for a column.

**Parameters:**

- `column_name` (str): Column name

**Returns:**

- `dict`: Quality lineage information

**Example:**

```python
quality = tracker.get_quality_lineage('customer_email')
print(f"Quality checks: {quality['checks']}")
```

### Performance Methods

#### `set_tracking_level(level, custom_config=None)`

Set the level of lineage tracking detail.

**Parameters:**

- `level` (str): Tracking level ('detailed', 'lightweight', 'custom')
- `custom_config` (dict, optional): Custom configuration for 'custom' level

**Example:**

```python
# Lightweight tracking for performance
tracker.set_tracking_level('lightweight')

# Custom tracking configuration
tracker.set_tracking_level('custom', {
    'track_operations': True,
    'track_metadata': False,
    'track_performance': True
})
```

#### `set_batch_mode(enabled, batch_size=1000)`

Enable or disable batch processing mode.

**Parameters:**

- `enabled` (bool): Whether to enable batch mode
- `batch_size` (int): Number of operations per batch

**Example:**

```python
tracker.set_batch_mode(True, batch_size=500)
```

#### `get_performance_metrics()`

Get performance metrics for the tracker.

**Returns:**

- `dict`: Performance metrics

**Example:**

```python
metrics = tracker.get_performance_metrics()
print(f"Average operation time: {metrics['avg_operation_time']}ms")
```

---

## DataFrameWrapper

A transparent wrapper around pandas DataFrames that automatically tracks lineage.

### Constructor

#### `DataFrameWrapper(dataframe, tracker, name, metadata=None)`

Create a lineage-tracked DataFrame wrapper.

**Parameters:**

- `dataframe` (pd.DataFrame): DataFrame to wrap
- `tracker` (LineageTracker): Lineage tracker instance
- `name` (str): Unique name for this DataFrame
- `metadata` (dict, optional): Additional metadata

**Example:**

```python
df_wrapped = DataFrameWrapper(
    df,
    tracker,
    "customers",
    metadata={'source': 'database', 'table': 'customers'}
)
```

### Pandas DataFrame Methods

The DataFrameWrapper supports all pandas DataFrame methods. Here are the key ones with lineage tracking:

#### Selection Methods

##### `__getitem__(key)`

```python
# Column selection
series = df_wrapped['column_name']
subset = df_wrapped[['col1', 'col2']]

# Boolean indexing
filtered = df_wrapped[df_wrapped['age'] > 25]
```

##### `loc[indexer]`

```python
# Label-based selection
selected = df_wrapped.loc[df_wrapped['status'] == 'active']
specific = df_wrapped.loc[0:5, 'name':'age']
```

##### `iloc[indexer]`

```python
# Position-based selection
first_10 = df_wrapped.iloc[:10]
subset = df_wrapped.iloc[0:5, 1:3]
```

##### `query(expr)`

```python
# Query with expression
result = df_wrapped.query('age > 30 and score < 80')
```

#### Transformation Methods

##### `assign(**kwargs)`

```python
# Add computed columns
enhanced = df_wrapped.assign(
    total=df_wrapped['price'] * df_wrapped['quantity'],
    category=df_wrapped['score'].apply(lambda x: 'high' if x > 80 else 'low')
)
```

##### `apply(func, axis=0, **kwargs)`

```python
# Apply function to rows or columns
df_wrapped['processed'] = df_wrapped['text'].apply(process_function)
df_wrapped['combined'] = df_wrapped.apply(combine_function, axis=1)
```

##### `transform(func, **kwargs)`

```python
# Transform values
normalized = df_wrapped.groupby('category')['value'].transform(
    lambda x: (x - x.mean()) / x.std()
)
```

#### Aggregation Methods

##### `groupby(by, **kwargs)`

```python
# Group by operations
grouped = df_wrapped.groupby('category').agg({
    'amount': 'sum',
    'quantity': 'mean'
})
```

##### `agg(func, axis=0, **kwargs)`

```python
# Aggregate functions
summary = df_wrapped.agg({
    'price': ['min', 'max', 'mean'],
    'quantity': 'sum'
})
```

##### `pivot_table(values, index, columns, aggfunc, **kwargs)`

```python
# Pivot table
pivot = df_wrapped.pivot_table(
    values='amount',
    index='category',
    columns='month',
    aggfunc='sum'
)
```

#### Join Methods

##### `merge(right, how='inner', on=None, **kwargs)`

```python
# Merge DataFrames
result = df_wrapped.merge(
    other_df,
    on='customer_id',
    how='left'
)
```

##### `join(other, **kwargs)`

```python
# Join on index
joined = df_wrapped.join(other_df, rsuffix='_right')
```

#### Cleaning Methods

##### `dropna(**kwargs)`

```python
# Remove missing values
cleaned = df_wrapped.dropna(subset=['important_column'])
```

##### `fillna(value, **kwargs)`

```python
# Fill missing values
filled = df_wrapped.fillna({
    'age': df_wrapped['age'].mean(),
    'category': 'Unknown'
})
```

##### `drop_duplicates(**kwargs)`

```python
# Remove duplicates
unique = df_wrapped.drop_duplicates(subset=['customer_id'])
```

### Lineage-Specific Methods

#### `get_column_lineage(column_name)`

Get lineage for a specific column in this DataFrame.

**Parameters:**

- `column_name` (str): Column name

**Returns:**

- `dict`: Column lineage information

#### `get_operation_history()`

Get history of operations on this DataFrame.

**Returns:**

- `list`: List of operations

#### `track_custom_operation(source_columns, target_columns, operation_type, **kwargs)`

Manually track a custom operation.

**Parameters:**

- `source_columns` (list): Source columns
- `target_columns` (list): Target columns
- `operation_type` (str): Operation type
- `**kwargs`: Additional metadata

#### `visualize_lineage(**kwargs)`

Visualize lineage for this DataFrame.

#### `export_lineage(format='json')`

Export lineage for this DataFrame.

#### `to_pandas()`

Convert back to regular pandas DataFrame (loses lineage tracking).

**Returns:**

- `pd.DataFrame`: Regular pandas DataFrame

---

## LineageNode

Represents a node in the lineage graph.

### Constructor

#### `LineageNode(name, node_type, metadata=None)`

**Parameters:**

- `name` (str): Node name
- `node_type` (str): Type ('table', 'column', 'operation')
- `metadata` (dict, optional): Node metadata

### Properties

- `name` (str): Node name
- `node_type` (str): Node type
- `metadata` (dict): Node metadata
- `id` (str): Unique node identifier
- `created_at` (datetime): Creation timestamp

### Methods

#### `add_metadata(key, value)`

Add metadata to the node.

#### `get_metadata(key, default=None)`

Get metadata value.

#### `to_dict()`

Convert node to dictionary representation.

---

## LineageEdge

Represents an edge (relationship) in the lineage graph.

### Constructor

#### `LineageEdge(source_node, target_node, operation_type, metadata=None)`

**Parameters:**

- `source_node` (LineageNode): Source node
- `target_node` (LineageNode): Target node
- `operation_type` (str): Type of operation
- `metadata` (dict, optional): Edge metadata

### Properties

- `source_node` (LineageNode): Source node
- `target_node` (LineageNode): Target node
- `operation_type` (str): Operation type
- `metadata` (dict): Edge metadata
- `id` (str): Unique edge identifier
- `created_at` (datetime): Creation timestamp

### Methods

#### `add_metadata(key, value)`

Add metadata to the edge.

#### `get_metadata(key, default=None)`

Get metadata value.

#### `to_dict()`

Convert edge to dictionary representation.

---

## Utility Functions

### `register_lineage_function(inputs, outputs)`

Decorator to register custom functions for lineage tracking.

**Parameters:**

- `inputs` (list): Input column names
- `outputs` (list): Output column names

**Example:**

```python
@register_lineage_function(inputs=['price', 'tax_rate'], outputs=['total_price'])
def calculate_total_price(df):
    return df.assign(total_price=df['price'] * (1 + df['tax_rate']))
```

### `create_lineage_graph(tracker)`

Create a NetworkX graph from lineage data.

**Parameters:**

- `tracker` (LineageTracker): Tracker instance

**Returns:**

- `networkx.DiGraph`: NetworkX directed graph

### `validate_lineage_graph(graph)`

Validate a lineage graph for consistency.

**Parameters:**

- `graph` (networkx.DiGraph): Graph to validate

**Returns:**

- `dict`: Validation results

### `merge_lineage_graphs(graph1, graph2)`

Merge two lineage graphs.

**Parameters:**

- `graph1` (networkx.DiGraph): First graph
- `graph2` (networkx.DiGraph): Second graph

**Returns:**

- `networkx.DiGraph`: Merged graph

### `calculate_lineage_complexity(graph)`

Calculate complexity metrics for a lineage graph.

**Parameters:**

- `graph` (networkx.DiGraph): Lineage graph

**Returns:**

- `dict`: Complexity metrics

---

## Exception Classes

### `LineageError`

Base exception for lineage-related errors.

### `NodeNotFoundError`

Raised when a node is not found in the graph.

### `InvalidOperationError`

Raised when an invalid operation is attempted.

### `CircularDependencyError`

Raised when a circular dependency is detected.

### `ValidationError`

Raised when lineage validation fails.

---

## Constants

### Operation Types

```python
OPERATION_TYPES = [
    'filter',
    'transform',
    'aggregate',
    'join',
    'union',
    'pivot',
    'sort',
    'groupby',
    'calculation',
    'custom'
]
```

### Node Types

```python
NODE_TYPES = [
    'table',
    'column',
    'operation',
    'checkpoint'
]
```

### Tracking Levels

```python
TRACKING_LEVELS = [
    'detailed',    # Full tracking with metadata
    'lightweight', # Basic operations only
    'custom'       # User-defined configuration
]
```

---

_This completes the comprehensive API reference for DataLineagePy core functionality. Every class, method, parameter, and return value is documented with examples._ 📚🚀
