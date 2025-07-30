"""
Advanced example demonstrating DataLineagePy Phase 3 features.

This example showcases:
- Concatenation operations
- Drop and rename operations  
- Pivot and melt operations
- Advanced groupby aggregations
- Smart dependency detection
- Complex multi-step workflows
"""

from lineagepy import LineageDataFrame, LineageTracker
import pandas as pd


def main():
    print("🚀 DataLineagePy Phase 3 Advanced Features Demo")
    print("=" * 50)

    # Reset tracker for clean demo
    LineageTracker.reset_global_instance()

    # 1. Create multiple data sources
    print("\n1. Creating multiple data sources...")

    # Sales data
    sales_data = {
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'product_id': ['P001', 'P002', 'P001'],
        'quantity': [10, 15, 8],
        'unit_price': [25.0, 40.0, 25.0],
        'sales_rep': ['Alice', 'Bob', 'Alice']
    }

    # Customer data
    customer_data = {
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'customer_id': ['C001', 'C002', 'C001'],
        'region': ['North', 'South', 'North'],
        'customer_type': ['Premium', 'Standard', 'Premium']
    }

    # Returns data
    returns_data = {
        'date': ['2023-01-02'],
        'product_id': ['P002'],
        'returned_qty': [3],
        'reason': ['Defective']
    }

    sales_df = LineageDataFrame(
        sales_data, name="sales_data", source_type="database")
    customer_df = LineageDataFrame(
        customer_data, name="customer_data", source_type="database")
    returns_df = LineageDataFrame(
        returns_data, name="returns_data", source_type="database")

    print(f"   Sales data: {sales_df.shape}")
    print(f"   Customer data: {customer_df.shape}")
    print(f"   Returns data: {returns_df.shape}")

    # 2. Data cleaning and preparation
    print("\n2. Data cleaning and preparation...")

    # Rename columns for clarity
    sales_clean = sales_df.rename({
        'unit_price': 'price_per_unit',
        'sales_rep': 'representative'
    })
    print(f"   Renamed sales columns: {list(sales_clean.columns)}")

    # Calculate revenue with smart dependency detection
    sales_with_revenue = sales_clean.assign(
        total_revenue=lambda x: x['quantity'] * x['price_per_unit'],
        revenue_category=lambda x: x['total_revenue'].apply(
            lambda val: 'High' if val > 300 else 'Low'
        )
    )
    print(f"   Added revenue calculations: {sales_with_revenue.shape}")

    # 3. Data integration using concatenation and merging
    print("\n3. Data integration...")

    # Merge sales with customer data
    integrated_data = sales_with_revenue.merge(
        customer_df,
        on='date',
        how='inner'
    )
    print(f"   Merged sales and customer data: {integrated_data.shape}")

    # Merge with returns data (left join to keep all sales)
    full_data = integrated_data.merge(
        returns_df,
        on=['date', 'product_id'],
        how='left'
    )
    print(f"   Merged with returns data: {full_data.shape}")

    # Fill missing return quantities with 0
    full_data_clean = full_data.assign(
        returned_qty=lambda x: x['returned_qty'].fillna(0),
        net_quantity=lambda x: x['quantity'] - x['returned_qty'].fillna(0)
    )

    # 4. Advanced aggregations
    print("\n4. Advanced aggregations...")

    # Group by multiple dimensions
    region_summary = full_data_clean.groupby(['region', 'customer_type']).agg({
        'total_revenue': ['sum', 'mean', 'count'],
        'net_quantity': 'sum',
        'returned_qty': 'sum'
    }).reset_index()
    print(f"   Region/customer summary: {region_summary.shape}")

    # Product performance analysis
    product_performance = full_data_clean.groupby('product_id').agg({
        'total_revenue': 'sum',
        'quantity': 'sum',
        'returned_qty': 'sum'
    }).reset_index()

    # Calculate return rate
    product_performance = product_performance.assign(
        return_rate=lambda x: x['returned_qty'] / x['quantity'] * 100
    )
    print(f"   Product performance: {product_performance.shape}")

    # 5. Pivot analysis
    print("\n5. Pivot analysis...")

    # Create pivot table for region vs customer type revenue
    revenue_pivot = full_data_clean.pivot_table(
        values='total_revenue',
        index='region',
        columns='customer_type',
        aggfunc='sum',
        fill_value=0
    )
    print(f"   Revenue pivot table: {revenue_pivot.shape}")
    print("   Pivot table preview:")
    print(revenue_pivot._df.to_string())

    # 6. Melt for analysis
    print("\n6. Melt transformation...")

    # Prepare data for melting
    metrics_data = product_performance[[
        'product_id', 'total_revenue', 'quantity', 'returned_qty']]

    # Melt to long format for visualization
    melted_metrics = metrics_data.melt(
        id_vars=['product_id'],
        value_vars=['total_revenue', 'quantity', 'returned_qty'],
        var_name='metric_type',
        value_name='metric_value'
    )
    print(f"   Melted metrics: {melted_metrics.shape}")

    # 7. Data filtering and selection
    print("\n7. Data filtering and selection...")

    # Filter high-value transactions
    high_value = full_data_clean[full_data_clean._df['total_revenue'] > 200]
    print(f"   High-value transactions: {high_value.shape}")

    # Select specific columns for final report
    final_report = high_value[['date', 'product_id',
                               'region', 'total_revenue', 'net_quantity']]
    print(f"   Final report columns: {list(final_report.columns)}")

    # 8. Concatenation example
    print("\n8. Concatenation example...")

    # Split data by region for processing
    north_data = full_data_clean[full_data_clean._df['region'] == 'North']
    south_data = full_data_clean[full_data_clean._df['region'] == 'South']

    # Process each region separately (example: add region-specific markup)
    north_processed = north_data.assign(
        markup_rate=0.15,
        final_price=lambda x: x['price_per_unit'] * (1 + x['markup_rate'])
    )

    south_processed = south_data.assign(
        markup_rate=0.12,
        final_price=lambda x: x['price_per_unit'] * (1 + x['markup_rate'])
    )

    # Concatenate back together
    combined_processed = LineageDataFrame.concat(
        [north_processed, south_processed])
    print(f"   Combined processed data: {combined_processed.shape}")

    # 9. Lineage analysis
    print("\n9. Lineage Analysis")
    print("-" * 20)

    tracker = LineageTracker.get_global_instance()
    stats = tracker.get_stats()

    print(f"   📊 Total nodes tracked: {stats['total_nodes']}")
    print(f"   📊 Total transformations: {stats['total_edges']}")
    print(f"   📊 Graph density: {stats['graph_density']:.3f}")

    # Analyze lineage for key columns
    print("\n   🔍 Column lineage analysis:")

    # Analyze final_price lineage
    final_price_lineage = combined_processed.get_lineage_for_column(
        'final_price')
    print(
        f"      'final_price' sources: {final_price_lineage.get('source_columns', [])}")

    # Analyze total_revenue lineage
    revenue_lineage = combined_processed.get_lineage_for_column(
        'total_revenue')
    print(
        f"      'total_revenue' sources: {revenue_lineage.get('source_columns', [])}")

    # Table lineage
    table_lineage = combined_processed.get_table_lineage()
    print(
        f"      Final table depends on {len(table_lineage.get('all_dependencies', []))} upstream tables")

    # 10. Operation type analysis
    print("\n   🔍 Transformation analysis:")
    operation_counts = {}
    for edge in tracker.edges.values():
        op_type = edge.transformation_type.value
        operation_counts[op_type] = operation_counts.get(op_type, 0) + 1

    for op_type, count in sorted(operation_counts.items()):
        print(f"      {op_type}: {count} operations")

    print("\n✅ Phase 3 advanced demo completed!")
    print("\n💡 Features demonstrated:")
    print("   • Concatenation of multiple DataFrames")
    print("   • Column renaming with lineage preservation")
    print("   • Drop operations for data cleaning")
    print("   • Pivot tables for cross-tabulation analysis")
    print("   • Melt operations for data reshaping")
    print("   • Advanced groupby with multiple aggregations")
    print("   • Smart dependency detection in assign operations")
    print("   • Complex multi-step data workflows")
    print("   • Comprehensive lineage tracking and analysis")


if __name__ == "__main__":
    main()
