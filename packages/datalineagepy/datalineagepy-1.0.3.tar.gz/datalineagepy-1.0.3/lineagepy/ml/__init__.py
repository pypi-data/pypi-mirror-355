"""
Machine Learning module for advanced anomaly detection in data lineage.

This module provides:
- Statistical anomaly detection
- ML-based pattern recognition
- Drift detection in data transformations
- Predictive quality assessment
- Automated threshold learning
"""

from .anomaly_detector import (
    AnomalyDetector,
    StatisticalDetector,
    MLAnomalyDetector,
    EnsembleDetector
)
from .drift_detector import (
    DriftDetector,
    SchemaDetector,
    DistributionDetector,
    VolumeDetector
)
from .pattern_analyzer import (
    PatternAnalyzer,
    TransformationPatternAnalyzer,
    UsagePatternAnalyzer
)
from .quality_predictor import (
    QualityPredictor,
    LineageQualityPredictor
)

__all__ = [
    # Anomaly detection
    'AnomalyDetector',
    'StatisticalDetector',
    'MLAnomalyDetector',
    'EnsembleDetector',

    # Drift detection
    'DriftDetector',
    'SchemaDetector',
    'DistributionDetector',
    'VolumeDetector',

    # Pattern analysis
    'PatternAnalyzer',
    'TransformationPatternAnalyzer',
    'UsagePatternAnalyzer',

    # Quality prediction
    'QualityPredictor',
    'LineageQualityPredictor',
]
