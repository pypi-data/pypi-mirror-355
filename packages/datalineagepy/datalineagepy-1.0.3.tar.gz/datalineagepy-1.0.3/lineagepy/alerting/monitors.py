"""
Monitoring components for the real-time alerting system.
"""

import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import logging

from ..core.tracker import LineageTracker
from .alert_manager import AlertManager, AlertRule, AlertSeverity

logger = logging.getLogger(__name__)


class Monitor(ABC):
    """Base class for monitoring components."""

    def __init__(self, alert_manager: AlertManager, check_interval: int = 30):
        """
        Initialize monitor.

        Args:
            alert_manager: AlertManager instance
            check_interval: Check interval in seconds
        """
        self.alert_manager = alert_manager
        self.check_interval = check_interval
        self.is_running = False
        self._monitor_thread: Optional[threading.Thread] = None

    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics for monitoring.

        Returns:
            Dictionary of collected metrics
        """
        pass

    def start(self) -> None:
        """Start the monitor."""
        if self.is_running:
            return

        self.is_running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Started {self.__class__.__name__}")

    def stop(self) -> None:
        """Stop the monitor."""
        self.is_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info(f"Stopped {self.__class__.__name__}")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running:
            try:
                metrics = self.collect_metrics()
                alerts = self.alert_manager.check_conditions(metrics)

                for alert in alerts:
                    self.alert_manager.send_alert(alert)

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(
                    f"Error in {self.__class__.__name__} monitoring: {str(e)}")
                time.sleep(self.check_interval)


class PerformanceMonitor(Monitor):
    """Monitor for performance metrics."""

    def __init__(self, alert_manager: AlertManager, tracker: LineageTracker,
                 check_interval: int = 30):
        """
        Initialize performance monitor.

        Args:
            alert_manager: AlertManager instance
            tracker: LineageTracker instance
            check_interval: Check interval in seconds
        """
        super().__init__(alert_manager, check_interval)
        self.tracker = tracker
        self.last_operation_count = 0
        self.last_check_time = datetime.now()

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics."""
        try:
            current_time = datetime.now()

            # Get current tracker statistics
            stats = self.tracker.get_statistics()

            # Calculate operations per second
            current_operations = stats.get('total_transformations', 0)
            time_delta = (current_time - self.last_check_time).total_seconds()

            if time_delta > 0:
                ops_per_second = (current_operations -
                                  self.last_operation_count) / time_delta
            else:
                ops_per_second = 0

            # Update for next iteration
            self.last_operation_count = current_operations
            self.last_check_time = current_time

            return {
                'node_count': stats.get('total_nodes', 0),
                'edge_count': stats.get('total_edges', 0),
                'transformation_count': stats.get('total_transformations', 0),
                'operations_per_second': ops_per_second,
                'memory_nodes': len(self.tracker.nodes),
                'memory_edges': len(self.tracker.edges),
                'timestamp': current_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {str(e)}")
            return {}


class QualityMonitor(Monitor):
    """Monitor for data quality metrics."""

    def __init__(self, alert_manager: AlertManager, tracker: LineageTracker,
                 check_interval: int = 60):
        """
        Initialize quality monitor.

        Args:
            alert_manager: AlertManager instance
            tracker: LineageTracker instance
            check_interval: Check interval in seconds
        """
        super().__init__(alert_manager, check_interval)
        self.tracker = tracker

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect quality metrics."""
        try:
            from ..testing.validators import QualityValidator

            validator = QualityValidator(self.tracker)
            quality_results = validator.validate_quality()

            # Extract quality metrics
            completeness_score = quality_results.get('completeness_score', 1.0)
            context_coverage = quality_results.get('context_coverage', 1.0)

            # Calculate overall quality score
            quality_score = (completeness_score + context_coverage) / 2

            return {
                'completeness_score': completeness_score,
                'context_coverage': context_coverage,
                'quality_score': quality_score,
                'total_nodes': quality_results.get('total_nodes', 0),
                'nodes_with_context': quality_results.get('nodes_with_context', 0),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to collect quality metrics: {str(e)}")
            return {}


class AnomalyMonitor(Monitor):
    """Monitor for anomaly detection."""

    def __init__(self, alert_manager: AlertManager, tracker: LineageTracker,
                 check_interval: int = 60):
        """
        Initialize anomaly monitor.

        Args:
            alert_manager: AlertManager instance  
            tracker: LineageTracker instance
            check_interval: Check interval in seconds
        """
        super().__init__(alert_manager, check_interval)
        self.tracker = tracker

        # Initialize anomaly detector
        try:
            from ..ml.anomaly_detector import EnsembleDetector
            self.anomaly_detector = EnsembleDetector()
            self._train_detector()
        except ImportError:
            logger.warning("ML anomaly detection not available")
            self.anomaly_detector = None

    def _train_detector(self) -> None:
        """Train the anomaly detector with historical data."""
        if self.anomaly_detector:
            try:
                # Get current statistics as training data
                stats = self.tracker.get_statistics()
                self.anomaly_detector.fit(stats)
                logger.info("Anomaly detector trained")
            except Exception as e:
                logger.error(f"Failed to train anomaly detector: {str(e)}")

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics and detect anomalies."""
        try:
            # Get current statistics
            stats = self.tracker.get_statistics()

            metrics = {
                'node_count': stats.get('total_nodes', 0),
                'edge_count': stats.get('total_edges', 0),
                'transformation_count': stats.get('total_transformations', 0),
                'timestamp': datetime.now().isoformat()
            }

            # Detect anomalies if detector is available
            if self.anomaly_detector:
                try:
                    anomalies = self.anomaly_detector.detect(metrics)

                    # Convert anomalies to alert data
                    if anomalies:
                        anomaly_data = []
                        for anomaly in anomalies:
                            anomaly_data.append({
                                'id': anomaly.id,
                                'type': anomaly.anomaly_type,
                                'severity': anomaly.severity,
                                'confidence': anomaly.confidence,
                                'description': anomaly.description
                            })

                        metrics['anomalies'] = anomaly_data
                        metrics['anomaly_count'] = len(anomalies)
                        metrics['max_severity'] = max(
                            a.severity for a in anomalies)
                    else:
                        metrics['anomalies'] = []
                        metrics['anomaly_count'] = 0
                        metrics['max_severity'] = 0.0

                except Exception as e:
                    logger.error(f"Anomaly detection failed: {str(e)}")
                    metrics['anomaly_error'] = str(e)

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect anomaly metrics: {str(e)}")
            return {}


class LineageMonitor(Monitor):
    """Monitor for general lineage health."""

    def __init__(self, alert_manager: AlertManager, tracker: LineageTracker,
                 check_interval: int = 120):
        """
        Initialize lineage monitor.

        Args:
            alert_manager: AlertManager instance
            tracker: LineageTracker instance
            check_interval: Check interval in seconds
        """
        super().__init__(alert_manager, check_interval)
        self.tracker = tracker
        self.baseline_metrics = {}

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect lineage health metrics."""
        try:
            stats = self.tracker.get_statistics()

            # Calculate graph metrics
            graph = self.tracker.get_networkx_graph()

            if graph.number_of_nodes() > 0:
                # Graph topology metrics
                density = graph.number_of_edges() / max(1, graph.number_of_nodes()
                                                        * (graph.number_of_nodes() - 1))
                avg_degree = sum(dict(graph.degree()).values()) / \
                    max(1, graph.number_of_nodes())

                # Connected components
                num_components = len(list(graph.connected_components())) if hasattr(
                    graph, 'connected_components') else 1

                # Path metrics
                try:
                    import networkx as nx
                    if nx.is_directed_acyclic_graph(graph):
                        is_dag = True
                    else:
                        is_dag = False
                except:
                    is_dag = True  # Assume DAG if can't verify
            else:
                density = 0
                avg_degree = 0
                num_components = 0
                is_dag = True

            metrics = {
                'total_nodes': stats.get('total_nodes', 0),
                'total_edges': stats.get('total_edges', 0),
                'total_transformations': stats.get('total_transformations', 0),
                'graph_density': density,
                'avg_degree': avg_degree,
                'num_components': num_components,
                'is_dag': is_dag,
                'timestamp': datetime.now().isoformat()
            }

            # Update baseline if not set
            if not self.baseline_metrics:
                self.baseline_metrics = metrics.copy()

            # Calculate deltas from baseline
            for key in ['total_nodes', 'total_edges', 'total_transformations']:
                if key in metrics and key in self.baseline_metrics:
                    metrics[f'{key}_delta'] = metrics[key] - \
                        self.baseline_metrics[key]

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect lineage metrics: {str(e)}")
            return {}
