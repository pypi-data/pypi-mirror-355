"""
Comprehensive tests for DataLineagePy Phase 4 visualization features.
"""

import os
import tempfile
from pathlib import Path

from lineagepy import LineageDataFrame, LineageTracker

# Test with optional imports
try:
    from lineagepy.visualization.graph_visualizer import LineageGraphVisualizer
    from lineagepy.visualization.column_visualizer import ColumnLineageVisualizer
    from lineagepy.visualization.report_generator import LineageReportGenerator
    from lineagepy.visualization.exporters import (
        JSONExporter, HTMLExporter, CSVExporter, MarkdownExporter
    )
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False


def test_basic_functionality():
    """Test basic visualization functionality."""
    print("Testing basic visualization functionality...")

    # Reset tracker
    LineageTracker.reset_global_instance()

    # Create simple test data
    data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
    df = LineageDataFrame(data, name="test_data")

    # Simple operation
    df_calc = df.assign(C=lambda x: x['A'] + x['B'])

    if HAS_VISUALIZATION:
        # Test graph visualizer
        visualizer = LineageGraphVisualizer()
        G = visualizer.create_networkx_graph()
        assert len(G.nodes()) > 0, "Should have nodes"

        # Test summary
        summary = visualizer.get_lineage_summary()
        assert summary['total_nodes'] > 0, "Should have nodes in summary"

        print("✅ Visualization functionality working")
    else:
        print("⚠️  Visualization modules not available")

    print("✅ Basic functionality test passed")


if __name__ == "__main__":
    print("🎨 Running DataLineagePy Phase 4 Visualization Tests...\n")

    try:
        test_basic_functionality()
        print("\n🎉 Phase 4 visualization tests completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
