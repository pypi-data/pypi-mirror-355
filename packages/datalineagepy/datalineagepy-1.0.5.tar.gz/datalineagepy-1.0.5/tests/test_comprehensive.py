"""
Comprehensive tests for DataLineagePy Phase 2.
"""

import pandas as pd
from lineagepy import LineageDataFrame, LineageTracker, configure_lineage


def test_basic_creation():
    """Test basic LineageDataFrame creation."""
    print("Testing basic creation...")

    data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
    ldf = LineageDataFrame(data, name="test_data")

    assert ldf.shape == (3, 2)
    assert list(ldf.columns) == ['A', 'B']
    print("✅ Basic creation test passed")


def demo_workflow():
    """Demonstrate basic workflow."""
    print("\n🔄 Running workflow demo...")

    # Create sample data
    sales_data = {
        'product': ['A', 'B', 'A', 'B'],
        'quantity': [10, 15, 8, 12],
        'price': [100, 200, 100, 200]
    }

    sales_df = LineageDataFrame(sales_data, name="sales_data")
    print(f"Created sales data: {sales_df.shape}")

    # Calculate total value
    sales_with_total = sales_df.assign(
        total_value=lambda x: x['quantity'] * x['price'])
    print(f"Added total_value column: {sales_with_total.shape}")

    print("✅ Workflow demo completed")


if __name__ == "__main__":
    print("🧪 Running DataLineagePy Phase 2 Tests...\n")

    try:
        test_basic_creation()
        demo_workflow()
        print("\n🎉 All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
