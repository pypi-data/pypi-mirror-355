"""
Predefined alert rules for common monitoring scenarios.
"""

from typing import Dict, Any, Callable
from .alert_manager import AlertRule, AlertSeverity


class PerformanceRule:
    """Factory for performance-related alert rules."""

    @staticmethod
    def high_operation_rate(threshold: float = 1000.0, severity: AlertSeverity = AlertSeverity.MEDIUM) -> AlertRule:
        """
        Create rule for high operation rate.

        Args:
            threshold: Operations per second threshold
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            ops_per_second = data.get('operations_per_second', 0)
            return ops_per_second > threshold

        return AlertRule(
            id="high_operation_rate",
            name="High Operation Rate",
            description=f"Operations per second exceeded {threshold}",
            severity=severity,
            condition=condition,
            cooldown_minutes=5,
            channels=["console"]
        )

    @staticmethod
    def memory_usage_high(threshold: int = 10000, severity: AlertSeverity = AlertSeverity.HIGH) -> AlertRule:
        """
        Create rule for high memory usage.

        Args:
            threshold: Number of nodes/edges threshold
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            memory_nodes = data.get('memory_nodes', 0)
            memory_edges = data.get('memory_edges', 0)
            total_memory_objects = memory_nodes + memory_edges
            return total_memory_objects > threshold

        return AlertRule(
            id="memory_usage_high",
            name="High Memory Usage",
            description=f"Memory objects exceeded {threshold}",
            severity=severity,
            condition=condition,
            cooldown_minutes=10,
            channels=["console"]
        )

    @staticmethod
    def slow_transformation(threshold: float = 5.0, severity: AlertSeverity = AlertSeverity.MEDIUM) -> AlertRule:
        """
        Create rule for slow transformations.

        Args:
            threshold: Execution time threshold in seconds
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            execution_time = data.get('execution_time', 0)
            return execution_time > threshold

        return AlertRule(
            id="slow_transformation",
            name="Slow Transformation",
            description=f"Transformation execution time exceeded {threshold} seconds",
            severity=severity,
            condition=condition,
            cooldown_minutes=3,
            channels=["console"]
        )


class QualityRule:
    """Factory for quality-related alert rules."""

    @staticmethod
    def low_completeness(threshold: float = 0.8, severity: AlertSeverity = AlertSeverity.HIGH) -> AlertRule:
        """
        Create rule for low completeness score.

        Args:
            threshold: Completeness score threshold (0.0 to 1.0)
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            completeness = data.get('completeness_score', 1.0)
            return completeness < threshold

        return AlertRule(
            id="low_completeness",
            name="Low Completeness Score",
            description=f"Completeness score dropped below {threshold}",
            severity=severity,
            condition=condition,
            cooldown_minutes=15,
            channels=["console"]
        )

    @staticmethod
    def poor_context_coverage(threshold: float = 0.7, severity: AlertSeverity = AlertSeverity.MEDIUM) -> AlertRule:
        """
        Create rule for poor context coverage.

        Args:
            threshold: Context coverage threshold (0.0 to 1.0)
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            coverage = data.get('context_coverage', 1.0)
            return coverage < threshold

        return AlertRule(
            id="poor_context_coverage",
            name="Poor Context Coverage",
            description=f"Context coverage dropped below {threshold}",
            severity=severity,
            condition=condition,
            cooldown_minutes=20,
            channels=["console"]
        )

    @staticmethod
    def overall_quality_degradation(threshold: float = 0.75, severity: AlertSeverity = AlertSeverity.HIGH) -> AlertRule:
        """
        Create rule for overall quality degradation.

        Args:
            threshold: Overall quality threshold (0.0 to 1.0)
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            quality = data.get('quality_score', 1.0)
            return quality < threshold

        return AlertRule(
            id="overall_quality_degradation",
            name="Overall Quality Degradation",
            description=f"Overall quality score dropped below {threshold}",
            severity=severity,
            condition=condition,
            cooldown_minutes=30,
            channels=["console"]
        )


class AnomalyRule:
    """Factory for anomaly-related alert rules."""

    @staticmethod
    def anomaly_detected(severity_threshold: float = 0.7, severity: AlertSeverity = AlertSeverity.HIGH) -> AlertRule:
        """
        Create rule for anomaly detection.

        Args:
            severity_threshold: Minimum anomaly severity to trigger alert
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            max_severity = data.get('max_severity', 0.0)
            anomaly_count = data.get('anomaly_count', 0)
            return anomaly_count > 0 and max_severity >= severity_threshold

        return AlertRule(
            id="anomaly_detected",
            name="Anomaly Detected",
            description=f"Anomaly with severity >= {severity_threshold} detected",
            severity=severity,
            condition=condition,
            cooldown_minutes=10,
            channels=["console"]
        )

    @staticmethod
    def multiple_anomalies(count_threshold: int = 3, severity: AlertSeverity = AlertSeverity.CRITICAL) -> AlertRule:
        """
        Create rule for multiple anomalies.

        Args:
            count_threshold: Minimum number of anomalies to trigger alert
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            anomaly_count = data.get('anomaly_count', 0)
            return anomaly_count >= count_threshold

        return AlertRule(
            id="multiple_anomalies",
            name="Multiple Anomalies",
            description=f"Multiple anomalies detected (>= {count_threshold})",
            severity=severity,
            condition=condition,
            cooldown_minutes=5,
            channels=["console"]
        )


class CustomRule:
    """Factory for custom alert rules."""

    @staticmethod
    def create_threshold_rule(rule_id: str, name: str, description: str,
                              metric_key: str, threshold: float, operator: str = '>',
                              severity: AlertSeverity = AlertSeverity.MEDIUM,
                              cooldown_minutes: int = 10) -> AlertRule:
        """
        Create a custom threshold-based rule.

        Args:
            rule_id: Unique rule identifier
            name: Rule name
            description: Rule description
            metric_key: Key in data dictionary to check
            threshold: Threshold value
            operator: Comparison operator ('>', '<', '>=', '<=', '==', '!=')
            severity: Alert severity
            cooldown_minutes: Cooldown period in minutes

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            value = data.get(metric_key, 0)

            if operator == '>':
                return value > threshold
            elif operator == '<':
                return value < threshold
            elif operator == '>=':
                return value >= threshold
            elif operator == '<=':
                return value <= threshold
            elif operator == '==':
                return value == threshold
            elif operator == '!=':
                return value != threshold
            else:
                return False

        return AlertRule(
            id=rule_id,
            name=name,
            description=description,
            severity=severity,
            condition=condition,
            cooldown_minutes=cooldown_minutes,
            channels=["console"]
        )

    @staticmethod
    def create_composite_rule(rule_id: str, name: str, description: str,
                              conditions: list, logic: str = 'AND',
                              severity: AlertSeverity = AlertSeverity.MEDIUM) -> AlertRule:
        """
        Create a composite rule with multiple conditions.

        Args:
            rule_id: Unique rule identifier
            name: Rule name
            description: Rule description
            conditions: List of condition functions
            logic: Logic operator ('AND', 'OR')
            severity: Alert severity

        Returns:
            AlertRule instance
        """
        def condition(data: Dict[str, Any]) -> bool:
            results = [cond(data) for cond in conditions]

            if logic.upper() == 'AND':
                return all(results)
            elif logic.upper() == 'OR':
                return any(results)
            else:
                return False

        return AlertRule(
            id=rule_id,
            name=name,
            description=description,
            severity=severity,
            condition=condition,
            cooldown_minutes=10,
            channels=["console"]
        )


class RulePresets:
    """Predefined rule presets for common scenarios."""

    @staticmethod
    def development_preset() -> list:
        """Get rules suitable for development environment."""
        return [
            PerformanceRule.memory_usage_high(
                threshold=1000, severity=AlertSeverity.LOW),
            QualityRule.low_completeness(
                threshold=0.5, severity=AlertSeverity.MEDIUM),
            AnomalyRule.anomaly_detected(
                severity_threshold=0.8, severity=AlertSeverity.HIGH)
        ]

    @staticmethod
    def production_preset() -> list:
        """Get rules suitable for production environment."""
        return [
            PerformanceRule.high_operation_rate(
                threshold=500.0, severity=AlertSeverity.HIGH),
            PerformanceRule.memory_usage_high(
                threshold=5000, severity=AlertSeverity.CRITICAL),
            PerformanceRule.slow_transformation(
                threshold=3.0, severity=AlertSeverity.MEDIUM),
            QualityRule.low_completeness(
                threshold=0.9, severity=AlertSeverity.CRITICAL),
            QualityRule.poor_context_coverage(
                threshold=0.8, severity=AlertSeverity.HIGH),
            QualityRule.overall_quality_degradation(
                threshold=0.85, severity=AlertSeverity.CRITICAL),
            AnomalyRule.anomaly_detected(
                severity_threshold=0.6, severity=AlertSeverity.HIGH),
            AnomalyRule.multiple_anomalies(
                count_threshold=2, severity=AlertSeverity.CRITICAL)
        ]

    @staticmethod
    def monitoring_preset() -> list:
        """Get rules suitable for continuous monitoring."""
        return [
            PerformanceRule.high_operation_rate(
                threshold=1000.0, severity=AlertSeverity.MEDIUM),
            PerformanceRule.memory_usage_high(
                threshold=10000, severity=AlertSeverity.HIGH),
            QualityRule.low_completeness(
                threshold=0.7, severity=AlertSeverity.MEDIUM),
            AnomalyRule.anomaly_detected(
                severity_threshold=0.7, severity=AlertSeverity.MEDIUM)
        ]
