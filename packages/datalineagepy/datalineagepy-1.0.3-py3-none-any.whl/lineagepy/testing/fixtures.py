"""
Test fixtures for common lineage testing scenarios.
"""

from typing import Dict, List, Tuple
from ..core.dataframe_wrapper import LineageDataFrame
from .generators import TestDataGenerator


def sample_dataframes() -> Dict[str, LineageDataFrame]:
    """
    Create a set of sample DataFrames for testing.

    Returns:
        Dictionary of sample DataFrames
    """
    generator = TestDataGenerator(seed=42)

    return {
        'simple': generator.generate_simple_dataframe(name="simple", rows=50),
        'medium': generator.generate_simple_dataframe(name="medium", rows=500, columns=['X', 'Y', 'Z', 'W']),
        'large': generator.generate_simple_dataframe(name="large", rows=2000, columns=[f'col_{i}' for i in range(10)])
    }


def complex_pipeline() -> Tuple[LineageDataFrame, Dict[str, LineageDataFrame]]:
    """
    Create a complex data pipeline for testing.

    Returns:
        Tuple of (final_result, intermediate_dataframes)
    """
    generator = TestDataGenerator(seed=42)

    # Generate base data
    sales_df, customers_df, products_df = generator.generate_sales_data(
        rows=500)

    # Build complex pipeline
    intermediates = {}

    # Step 1: Enrich sales with customer data
    enriched_sales = sales_df.merge(customers_df, on='customer_id', how='left')
    intermediates['enriched_sales'] = enriched_sales

    # Step 2: Add product information
    complete_sales = enriched_sales.merge(
        products_df, on='product_id', how='left')
    intermediates['complete_sales'] = complete_sales

    # Step 3: Calculate derived columns
    sales_with_calc = complete_sales.assign(
        total_amount=lambda x: x['quantity'] * x['unit_price'],
        discount_amount=lambda x: x['quantity'] *
        x['unit_price'] * x['discount_percent'] / 100
    )
    intermediates['sales_with_calc'] = sales_with_calc

    # Step 4: Final amount calculation
    final_sales = sales_with_calc.assign(
        final_amount=lambda x: x['total_amount'] - x['discount_amount']
    )
    intermediates['final_sales'] = final_sales

    # Step 5: Aggregation by tier and category
    summary = final_sales.groupby(['tier', 'category']).agg({
        'final_amount': ['sum', 'mean', 'count'],
        'quantity': 'sum'
    })

    return summary, intermediates


def large_dataset() -> LineageDataFrame:
    """
    Create a large dataset for performance testing.

    Returns:
        Large LineageDataFrame
    """
    generator = TestDataGenerator(seed=42)
    return generator.generate_large_dataset(rows=10000, columns=25)


def edge_case_data() -> Dict[str, LineageDataFrame]:
    """
    Create edge case datasets for robustness testing.

    Returns:
        Dictionary of edge case DataFrames
    """
    generator = TestDataGenerator(seed=42)
    return generator.generate_edge_case_data()
