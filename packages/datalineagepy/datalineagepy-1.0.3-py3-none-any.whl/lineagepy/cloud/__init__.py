"""
Multi-cloud integration module for DataLineagePy.

This module provides universal cloud management capabilities for tracking
data lineage across multiple cloud providers and data lake formats.
"""

from .universal_manager import UniversalCloudManager
from .cross_cloud_pipeline import CrossCloudPipeline
from .cost_optimizer import CloudCostOptimizer

__all__ = [
    'UniversalCloudManager',
    'CrossCloudPipeline',
    'CloudCostOptimizer'
]
