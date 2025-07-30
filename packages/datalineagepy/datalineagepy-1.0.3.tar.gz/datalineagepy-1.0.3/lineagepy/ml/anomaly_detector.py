"""
Advanced ML-based anomaly detection for data lineage.
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
import warnings

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.cluster import DBSCAN
    from sklearn.covariance import EllipticEnvelope
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning(
        "scikit-learn not available. ML-based anomaly detection will be limited.")


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    id: str
    timestamp: datetime
    anomaly_type: str
    severity: float  # 0.0 to 1.0
    description: str
    affected_nodes: List[str]
    metadata: Dict[str, Any]
    confidence: float  # 0.0 to 1.0


class AnomalyDetector(ABC):
    """Base class for anomaly detectors."""

    @abstractmethod
    def fit(self, data: Dict[str, Any]) -> None:
        """
        Train the anomaly detector.

        Args:
            data: Training data
        """
        pass

    @abstractmethod
    def detect(self, data: Dict[str, Any]) -> List[Anomaly]:
        """
        Detect anomalies in the provided data.

        Args:
            data: Data to analyze

        Returns:
            List of detected anomalies
        """
        pass


class StatisticalDetector(AnomalyDetector):
    """Statistical anomaly detector using traditional methods."""

    def __init__(self, window_size: int = 100, z_threshold: float = 3.0):
        """
        Initialize statistical detector.

        Args:
            window_size: Size of the sliding window for statistics
            z_threshold: Z-score threshold for anomaly detection
        """
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.metrics_history = defaultdict(lambda: deque(maxlen=window_size))
        self.baseline_stats = {}

    def fit(self, data: Dict[str, Any]) -> None:
        """Train the statistical detector."""
        # Extract metrics from historical data
        metrics = self._extract_metrics(data)

        # Update history
        for metric_name, value in metrics.items():
            self.metrics_history[metric_name].append(value)

        # Calculate baseline statistics
        self._update_baseline_stats()

    def detect(self, data: Dict[str, Any]) -> List[Anomaly]:
        """Detect statistical anomalies."""
        anomalies = []
        metrics = self._extract_metrics(data)

        for metric_name, current_value in metrics.items():
            if metric_name not in self.baseline_stats:
                continue

            mean = self.baseline_stats[metric_name]['mean']
            std = self.baseline_stats[metric_name]['std']

            if std > 0:
                z_score = abs((current_value - mean) / std)

                if z_score > self.z_threshold:
                    anomaly = Anomaly(
                        id=f"stat_{metric_name}_{int(datetime.now().timestamp())}",
                        timestamp=datetime.now(),
                        anomaly_type="statistical",
                        severity=min(z_score / self.z_threshold, 1.0),
                        description=f"Statistical anomaly in {metric_name}: z-score = {z_score:.2f}",
                        affected_nodes=data.get('affected_nodes', []),
                        metadata={
                            'metric': metric_name,
                            'current_value': current_value,
                            'expected_mean': mean,
                            'expected_std': std,
                            'z_score': z_score
                        },
                        confidence=min(z_score / (self.z_threshold * 2), 1.0)
                    )
                    anomalies.append(anomaly)

        # Update history with current metrics
        for metric_name, value in metrics.items():
            self.metrics_history[metric_name].append(value)

        self._update_baseline_stats()

        return anomalies

    def _extract_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical metrics from data."""
        metrics = {}

        # Basic lineage metrics
        if 'node_count' in data:
            metrics['node_count'] = float(data['node_count'])

        if 'edge_count' in data:
            metrics['edge_count'] = float(data['edge_count'])

        if 'transformation_count' in data:
            metrics['transformation_count'] = float(
                data['transformation_count'])

        # Performance metrics
        if 'execution_time' in data:
            metrics['execution_time'] = float(data['execution_time'])

        if 'memory_usage' in data:
            metrics['memory_usage'] = float(data['memory_usage'])

        # Data quality metrics
        if 'completeness_score' in data:
            metrics['completeness_score'] = float(data['completeness_score'])

        if 'context_coverage' in data:
            metrics['context_coverage'] = float(data['context_coverage'])

        return metrics

    def _update_baseline_stats(self) -> None:
        """Update baseline statistics from history."""
        for metric_name, history in self.metrics_history.items():
            if len(history) >= 10:  # Minimum samples for reliable statistics
                values = list(history)
                self.baseline_stats[metric_name] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }


class MLAnomalyDetector(AnomalyDetector):
    """ML-based anomaly detector using scikit-learn."""

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize ML anomaly detector.

        Args:
            contamination: Expected proportion of anomalies
            random_state: Random state for reproducibility
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required for ML-based anomaly detection")

        self.contamination = contamination
        self.random_state = random_state

        # Initialize models
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )

        self.elliptic_envelope = EllipticEnvelope(
            contamination=contamination,
            random_state=random_state
        )

        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% of variance

        self.is_fitted = False
        self.feature_names = []

    def fit(self, data: Dict[str, Any]) -> None:
        """Train the ML anomaly detector."""
        # Extract features from training data
        features = self._extract_features(data)

        if len(features) == 0:
            logger.warning("No features extracted for ML anomaly detection")
            return

        # Convert to numpy array
        X = np.array(features).reshape(
            1, -1) if len(np.array(features).shape) == 1 else np.array(features)

        if X.shape[0] < 10:
            logger.warning(
                "Insufficient training data for ML anomaly detection")
            return

        # Fit preprocessing
        X_scaled = self.scaler.fit_transform(X)

        # Apply PCA if we have enough features
        if X_scaled.shape[1] > 2:
            X_processed = self.pca.fit_transform(X_scaled)
        else:
            X_processed = X_scaled

        # Fit anomaly detection models
        try:
            self.isolation_forest.fit(X_processed)
            self.elliptic_envelope.fit(X_processed)
            self.is_fitted = True
            logger.info("ML anomaly detector trained successfully")
        except Exception as e:
            logger.error(f"Failed to train ML anomaly detector: {str(e)}")

    def detect(self, data: Dict[str, Any]) -> List[Anomaly]:
        """Detect ML-based anomalies."""
        if not self.is_fitted:
            return []

        anomalies = []
        features = self._extract_features(data)

        if len(features) == 0:
            return anomalies

        # Convert to numpy array
        X = np.array(features).reshape(1, -1)

        try:
            # Preprocess features
            X_scaled = self.scaler.transform(X)

            if hasattr(self.pca, 'transform'):
                X_processed = self.pca.transform(X_scaled)
            else:
                X_processed = X_scaled

            # Get predictions from both models
            iso_pred = self.isolation_forest.predict(X_processed)[0]
            iso_score = self.isolation_forest.decision_function(X_processed)[0]

            elliptic_pred = self.elliptic_envelope.predict(X_processed)[0]
            elliptic_score = self.elliptic_envelope.decision_function(X_processed)[
                0]

            # Check for anomalies
            if iso_pred == -1 or elliptic_pred == -1:
                # Calculate severity based on scores
                severity = max(
                    0.0, min(1.0, (abs(iso_score) + abs(elliptic_score)) / 2))
                confidence = 0.8 if (
                    iso_pred == -1 and elliptic_pred == -1) else 0.6

                anomaly = Anomaly(
                    id=f"ml_{int(datetime.now().timestamp())}",
                    timestamp=datetime.now(),
                    anomaly_type="ml_based",
                    severity=severity,
                    description=f"ML-based anomaly detected (ISO: {iso_pred}, EE: {elliptic_pred})",
                    affected_nodes=data.get('affected_nodes', []),
                    metadata={
                        'isolation_forest_score': float(iso_score),
                        'elliptic_envelope_score': float(elliptic_score),
                        'features': features
                    },
                    confidence=confidence
                )
                anomalies.append(anomaly)

        except Exception as e:
            logger.error(f"Error in ML anomaly detection: {str(e)}")

        return anomalies

    def _extract_features(self, data: Dict[str, Any]) -> List[float]:
        """Extract numerical features for ML models."""
        features = []

        # Lineage structure features
        features.extend([
            data.get('node_count', 0),
            data.get('edge_count', 0),
            data.get('transformation_count', 0),
            data.get('table_count', 0),
            data.get('column_count', 0)
        ])

        # Performance features
        features.extend([
            data.get('execution_time', 0),
            data.get('memory_usage', 0),
            data.get('cpu_usage', 0)
        ])

        # Quality features
        features.extend([
            data.get('completeness_score', 1.0),
            data.get('context_coverage', 1.0),
            data.get('quality_score', 1.0)
        ])

        # Graph topology features
        features.extend([
            data.get('graph_density', 0),
            data.get('avg_degree', 0),
            data.get('max_depth', 0)
        ])

        return [float(f) for f in features]


class EnsembleDetector(AnomalyDetector):
    """Ensemble anomaly detector combining multiple methods."""

    def __init__(self, detectors: Optional[List[AnomalyDetector]] = None):
        """
        Initialize ensemble detector.

        Args:
            detectors: List of anomaly detectors to ensemble
        """
        self.detectors = detectors or []

        # Add default detectors if none provided
        if not self.detectors:
            self.detectors.append(StatisticalDetector())
            if SKLEARN_AVAILABLE:
                self.detectors.append(MLAnomalyDetector())

    def fit(self, data: Dict[str, Any]) -> None:
        """Train all detectors in the ensemble."""
        for detector in self.detectors:
            try:
                detector.fit(data)
            except Exception as e:
                logger.error(
                    f"Failed to train detector {type(detector).__name__}: {str(e)}")

    def detect(self, data: Dict[str, Any]) -> List[Anomaly]:
        """Detect anomalies using ensemble voting."""
        all_anomalies = []

        # Collect anomalies from all detectors
        for detector in self.detectors:
            try:
                anomalies = detector.detect(data)
                all_anomalies.extend(anomalies)
            except Exception as e:
                logger.error(
                    f"Error in detector {type(detector).__name__}: {str(e)}")

        # Merge and rank anomalies
        merged_anomalies = self._merge_anomalies(all_anomalies)

        return merged_anomalies

    def _merge_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """Merge similar anomalies and rank by consensus."""
        if not anomalies:
            return []

        # Group anomalies by type and affected nodes
        groups = defaultdict(list)

        for anomaly in anomalies:
            key = (anomaly.anomaly_type, tuple(sorted(anomaly.affected_nodes)))
            groups[key].append(anomaly)

        # Create consensus anomalies
        consensus_anomalies = []

        for group_anomalies in groups.values():
            if len(group_anomalies) == 1:
                consensus_anomalies.append(group_anomalies[0])
            else:
                # Create consensus anomaly
                consensus = self._create_consensus_anomaly(group_anomalies)
                consensus_anomalies.append(consensus)

        # Sort by severity and confidence
        consensus_anomalies.sort(
            key=lambda x: (x.severity * x.confidence),
            reverse=True
        )

        return consensus_anomalies

    def _create_consensus_anomaly(self, anomalies: List[Anomaly]) -> Anomaly:
        """Create a consensus anomaly from multiple detections."""
        # Calculate weighted averages
        total_weight = sum(a.confidence for a in anomalies)

        if total_weight == 0:
            avg_severity = np.mean([a.severity for a in anomalies])
            avg_confidence = np.mean([a.confidence for a in anomalies])
        else:
            avg_severity = sum(
                a.severity * a.confidence for a in anomalies) / total_weight
            avg_confidence = sum(
                a.confidence * a.confidence for a in anomalies) / total_weight

        # Combine descriptions
        descriptions = [a.description for a in anomalies]
        combined_description = f"Consensus anomaly ({len(anomalies)} detectors): " + "; ".join(
            descriptions)

        # Combine metadata
        combined_metadata = {}
        for anomaly in anomalies:
            for key, value in anomaly.metadata.items():
                if key not in combined_metadata:
                    combined_metadata[key] = []
                combined_metadata[key].append(value)

        return Anomaly(
            id=f"consensus_{int(datetime.now().timestamp())}",
            timestamp=datetime.now(),
            anomaly_type="consensus",
            severity=avg_severity,
            description=combined_description,
            affected_nodes=anomalies[0].affected_nodes,
            metadata=combined_metadata,
            # Boost confidence for consensus
            confidence=min(avg_confidence * 1.2, 1.0)
        )
