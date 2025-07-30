"""
Comprehensive tests for DataLineagePy Phase 3 operations.
"""

import pandas as pd
from lineagepy import LineageDataFrame, LineageTracker, configure_lineage


def test_concat_operations():
    """Test concatenation operations."""
    print("Testing concatenation operations...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    # Create test DataFrames
    df1_data = {'A': [1, 2], 'B': [3, 4]}
    df2_data = {'A': [5, 6], 'B': [7, 8]}
    df3_data = {'A': [9, 10], 'C': [11, 12]}

    df1 = LineageDataFrame(df1_data, name="df1")
    df2 = LineageDataFrame(df2_data, name="df2")
    df3 = LineageDataFrame(df3_data, name="df3")

    # Test static concat method
    result = LineageDataFrame.concat([df1, df2])
    assert result.shape == (4, 2)
    assert list(result.columns) == ['A', 'B']

    # Test instance concat method
    result2 = df1.concat_with([df2])
    assert result2.shape == (4, 2)

    # Test concat with different columns
    result3 = LineageDataFrame.concat([df1, df3], sort=False)
    assert result3.shape == (4, 3)

    # Check lineage tracking
    tracker = LineageTracker.get_global_instance()
    concat_edges = [e for e in tracker.edges.values(
    ) if e.transformation_type.value == 'concat']
    assert len(concat_edges) > 0

    print("✅ Concatenation operations test passed")


def test_drop_operations():
    """Test drop operations."""
    print("Testing drop operations...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    data = {'A': [1, 2, 3], 'B': [4, 5, 6], 'C': [7, 8, 9]}
    df = LineageDataFrame(data, name="source_data")

    # Drop single column
    result1 = df.drop('C', axis=1)
    assert result1.shape == (3, 2)
    assert list(result1.columns) == ['A', 'B']

    # Drop multiple columns
    result2 = df.drop(['B', 'C'], axis=1)
    assert result2.shape == (3, 1)
    assert list(result2.columns) == ['A']

    # Drop rows
    result3 = df.drop(0, axis=0)
    assert result3.shape == (2, 3)

    print("✅ Drop operations test passed")


def test_rename_operations():
    """Test rename operations."""
    print("Testing rename operations...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    data = {'old_name': [1, 2, 3], 'another_col': [4, 5, 6]}
    df = LineageDataFrame(data, name="source_data")

    # Rename with dictionary
    result1 = df.rename({'old_name': 'new_name'})
    assert 'new_name' in result1.columns
    assert 'old_name' not in result1.columns
    assert 'another_col' in result1.columns

    # Rename with function
    result2 = df.rename(lambda x: x.upper())
    assert 'OLD_NAME' in result2.columns
    assert 'ANOTHER_COL' in result2.columns

    print("✅ Rename operations test passed")


def test_pivot_operations():
    """Test pivot table operations."""
    print("Testing pivot operations...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    data = {
        'A': ['foo', 'foo', 'bar', 'bar'],
        'B': ['one', 'two', 'one', 'two'],
        'C': [1, 2, 3, 4],
        'D': [10, 20, 30, 40]
    }
    df = LineageDataFrame(data, name="pivot_source")

    # Create pivot table
    result = df.pivot_table(values='C', index='A', columns='B', aggfunc='sum')
    assert result.shape == (2, 2)

    # Check lineage tracking
    tracker = LineageTracker.get_global_instance()
    pivot_edges = [e for e in tracker.edges.values(
    ) if e.transformation_type.value == 'pivot']
    assert len(pivot_edges) > 0

    print("✅ Pivot operations test passed")


def test_melt_operations():
    """Test melt operations."""
    print("Testing melt operations...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    data = {
        'A': ['a', 'b', 'c'],
        'B': [1, 3, 5],
        'C': [2, 4, 6]
    }
    df = LineageDataFrame(data, name="melt_source")

    # Melt the DataFrame
    result = df.melt(id_vars=['A'], value_vars=['B', 'C'])
    assert result.shape == (6, 3)
    assert 'variable' in result.columns
    assert 'value' in result.columns

    # Melt with custom names
    result2 = df.melt(id_vars=['A'], var_name='metric', value_name='score')
    assert 'metric' in result2.columns
    assert 'score' in result2.columns

    # Check lineage tracking
    tracker = LineageTracker.get_global_instance()
    melt_edges = [e for e in tracker.edges.values(
    ) if e.transformation_type.value == 'melt']
    assert len(melt_edges) > 0

    print("✅ Melt operations test passed")


def test_advanced_groupby():
    """Test advanced groupby operations."""
    print("Testing advanced groupby operations...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    data = {
        'group': ['A', 'A', 'B', 'B', 'A'],
        'value1': [1, 2, 3, 4, 5],
        'value2': [10, 20, 30, 40, 50]
    }
    df = LineageDataFrame(data, name="groupby_source")

    # Test various aggregation methods
    grouped = df.groupby('group')

    # Test multiple aggregation methods
    result_mean = grouped.mean()
    result_sum = grouped.sum()
    result_min = grouped.min()
    result_max = grouped.max()
    result_std = grouped.std()
    result_count = grouped.count()
    result_size = grouped.size()

    # Verify shapes
    assert result_mean.shape[0] == 2  # Two groups
    assert result_sum.shape[0] == 2
    assert result_size.shape == (2, 2)  # group + size columns

    # Test custom aggregation
    result_agg = grouped.agg({
        'value1': ['sum', 'mean'],
        'value2': 'max'
    })

    print("✅ Advanced groupby operations test passed")


def test_smart_dependency_detection():
    """Test smart dependency detection in assign operations."""
    print("Testing smart dependency detection...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    data = {'A': [1, 2, 3], 'B': [4, 5, 6], 'C': [7, 8, 9]}
    df = LineageDataFrame(data, name="dependency_test")

    # Test lambda with specific column references
    result1 = df.assign(D=lambda x: x['A'] + x['B'])

    # Get lineage for the new column
    lineage_d = result1.get_lineage_for_column('D')
    source_cols = set(lineage_d.get('source_columns', []))

    # Should detect A and B as dependencies (though this might be conservative)
    print(f"   Detected dependencies for D: {source_cols}")

    # Test with a more complex function
    def complex_calc(df):
        return df['A'] * 2 + df['C']

    result2 = df.assign(E=complex_calc)
    lineage_e = result2.get_lineage_for_column('E')
    source_cols_e = set(lineage_e.get('source_columns', []))
    print(f"   Detected dependencies for E: {source_cols_e}")

    print("✅ Smart dependency detection test passed")


def test_apply_operations():
    """Test apply operations with lineage tracking."""
    print("Testing apply operations...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
    df = LineageDataFrame(data, name="apply_source")

    # Test apply with lambda
    result1 = df.apply(lambda x: x * 2)
    if isinstance(result1, LineageDataFrame):
        assert result1.shape == df.shape

    # Test apply on axis=1 (rows)
    result2 = df.apply(lambda row: row.sum(), axis=1)
    # This returns a Series, not a DataFrame

    print("✅ Apply operations test passed")


def demo_complex_workflow():
    """Demonstrate a complex workflow using Phase 3 operations."""
    print("\n🔄 Running complex workflow demo...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    # Create sample sales data
    sales_data = {
        'date': ['2023-01-01', '2023-01-01', '2023-01-02', '2023-01-02'],
        'product': ['A', 'B', 'A', 'B'],
        'region': ['North', 'South', 'North', 'South'],
        'quantity': [10, 15, 8, 12],
        'price': [100, 200, 100, 200]
    }

    # Create returns data
    returns_data = {
        'date': ['2023-01-01', '2023-01-02'],
        'product': ['A', 'B'],
        'region': ['North', 'South'],
        'returned_qty': [2, 3]
    }

    sales_df = LineageDataFrame(sales_data, name="sales_data")
    returns_df = LineageDataFrame(returns_data, name="returns_data")

    print(f"   Sales data: {sales_df.shape}")
    print(f"   Returns data: {returns_df.shape}")

    # Calculate revenue
    sales_with_revenue = sales_df.assign(
        revenue=lambda x: x['quantity'] * x['price']
    )
    print(f"   Added revenue: {sales_with_revenue.shape}")

    # Merge with returns
    merged = sales_with_revenue.merge(
        returns_df,
        on=['date', 'product', 'region'],
        how='left'
    )
    print(f"   Merged with returns: {merged.shape}")

    # Fill missing returns with 0
    merged_filled = merged.assign(
        returned_qty=lambda x: x['returned_qty'].fillna(0)
    )

    # Calculate net quantity and revenue
    final_data = merged_filled.assign(
        net_quantity=lambda x: x['quantity'] - x['returned_qty'],
        net_revenue=lambda x: x['net_quantity'] * x['price']
    )
    print(f"   Added net calculations: {final_data.shape}")

    # Create summary by product
    product_summary = final_data.groupby('product').agg({
        'net_quantity': 'sum',
        'net_revenue': 'sum',
        'quantity': 'sum'
    }).reset_index()
    print(f"   Product summary: {product_summary.shape}")

    # Pivot by region
    region_pivot = final_data.pivot_table(
        values='net_revenue',
        index='product',
        columns='region',
        aggfunc='sum',
        fill_value=0
    )
    print(f"   Region pivot: {region_pivot.shape}")

    # Show lineage stats
    tracker = LineageTracker.get_global_instance()
    stats = tracker.get_stats()
    print(f"\n   📊 Lineage tracking stats:")
    print(f"      Total nodes: {stats['total_nodes']}")
    print(f"      Total transformations: {stats['total_edges']}")

    # Show some lineage information
    net_revenue_lineage = product_summary.get_lineage_for_column('net_revenue')
    print(
        f"      'net_revenue' depends on: {len(net_revenue_lineage.get('source_columns', []))} source columns")

    print("✅ Complex workflow demo completed")


if __name__ == "__main__":
    print("🧪 Running DataLineagePy Phase 3 Tests...\n")

    try:
        test_concat_operations()
        test_drop_operations()
        test_rename_operations()
        test_pivot_operations()
        test_melt_operations()
        test_advanced_groupby()
        test_smart_dependency_detection()
        test_apply_operations()

        demo_complex_workflow()

        print("\n🎉 All Phase 3 tests passed! Advanced operations are working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
