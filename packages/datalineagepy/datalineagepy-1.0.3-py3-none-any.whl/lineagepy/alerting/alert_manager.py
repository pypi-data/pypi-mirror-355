"""
Core alert manager for real-time monitoring and notifications.
"""

import time
import threading
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents an alert instance."""
    id: str
    rule_id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class AlertRule:
    """Defines an alert rule."""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: Callable[[Dict[str, Any]], bool]
    cooldown_minutes: int = 5
    enabled: bool = True
    channels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertManager:
    """
    Central alert manager for real-time monitoring and notifications.
    """

    def __init__(self):
        """Initialize the alert manager."""
        self.rules: Dict[str, AlertRule] = {}
        self.channels: Dict[str, Any] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_times: Dict[str, datetime] = {}
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Default console channel
        from .channels import ConsoleChannel
        self.add_channel("console", ConsoleChannel())

    def add_rule(self, rule: AlertRule) -> None:
        """
        Add an alert rule.

        Args:
            rule: AlertRule to add
        """
        with self._lock:
            self.rules[rule.id] = rule
            logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> None:
        """
        Remove an alert rule.

        Args:
            rule_id: ID of the rule to remove
        """
        with self._lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"Removed alert rule: {rule_id}")

    def add_channel(self, name: str, channel: Any) -> None:
        """
        Add a notification channel.

        Args:
            name: Name of the channel
            channel: Channel instance
        """
        with self._lock:
            self.channels[name] = channel
            logger.info(f"Added notification channel: {name}")

    def remove_channel(self, name: str) -> None:
        """
        Remove a notification channel.

        Args:
            name: Name of the channel to remove
        """
        with self._lock:
            if name in self.channels:
                del self.channels[name]
                logger.info(f"Removed notification channel: {name}")

    def check_conditions(self, data: Dict[str, Any]) -> List[Alert]:
        """
        Check all alert conditions against provided data.

        Args:
            data: Data to check against alert rules

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        current_time = datetime.now()

        with self._lock:
            for rule in self.rules.values():
                if not rule.enabled:
                    continue

                # Check cooldown
                last_alert_time = self.last_alert_times.get(rule.id)
                if last_alert_time:
                    cooldown_end = last_alert_time + \
                        timedelta(minutes=rule.cooldown_minutes)
                    if current_time < cooldown_end:
                        continue

                # Check condition
                try:
                    if rule.condition(data):
                        alert = self._create_alert(rule, data)
                        triggered_alerts.append(alert)
                        self.last_alert_times[rule.id] = current_time
                except Exception as e:
                    logger.error(f"Error checking rule {rule.id}: {str(e)}")

        return triggered_alerts

    def _create_alert(self, rule: AlertRule, data: Dict[str, Any]) -> Alert:
        """
        Create an alert from a rule and data.

        Args:
            rule: AlertRule that was triggered
            data: Data that triggered the rule

        Returns:
            Created Alert instance
        """
        alert_id = f"{rule.id}_{int(time.time())}"

        # Generate alert message
        message = f"Alert triggered: {rule.description}"
        if 'details' in data:
            message += f"\nDetails: {data['details']}"

        alert = Alert(
            id=alert_id,
            rule_id=rule.id,
            severity=rule.severity,
            title=rule.name,
            message=message,
            timestamp=datetime.now(),
            metadata=data.copy()
        )

        return alert

    def send_alert(self, alert: Alert) -> None:
        """
        Send an alert through configured channels.

        Args:
            alert: Alert to send
        """
        rule = self.rules.get(alert.rule_id)
        if not rule:
            return

        # Determine channels to use
        channels_to_use = rule.channels if rule.channels else ["console"]

        for channel_name in channels_to_use:
            channel = self.channels.get(channel_name)
            if channel:
                try:
                    channel.send_alert(alert)
                except Exception as e:
                    logger.error(
                        f"Failed to send alert via {channel_name}: {str(e)}")

        # Store alert
        with self._lock:
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an active alert.

        Args:
            alert_id: ID of the alert to resolve

        Returns:
            True if alert was resolved, False if not found
        """
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                del self.active_alerts[alert_id]
                logger.info(f"Resolved alert: {alert_id}")
                return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """
        Get all active alerts.

        Returns:
            List of active alerts
        """
        with self._lock:
            return list(self.active_alerts.values())

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """
        Get alert history for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            List of alerts from the specified period
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            return [alert for alert in self.alert_history
                    if alert.timestamp >= cutoff_time]

    def start_monitoring(self, interval_seconds: int = 30) -> None:
        """
        Start continuous monitoring.

        Args:
            interval_seconds: Monitoring interval in seconds
        """
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Started alert monitoring")

    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Stopped alert monitoring")

    def _monitor_loop(self, interval_seconds: int) -> None:
        """
        Main monitoring loop.

        Args:
            interval_seconds: Monitoring interval in seconds
        """
        while self._monitoring:
            try:
                # This would be called by monitors to check conditions
                # For now, it's a placeholder for the monitoring framework
                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(interval_seconds)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get alerting statistics.

        Returns:
            Dictionary with alerting statistics
        """
        with self._lock:
            total_rules = len(self.rules)
            enabled_rules = sum(
                1 for rule in self.rules.values() if rule.enabled)
            active_alerts = len(self.active_alerts)

            # Alert counts by severity
            severity_counts = {}
            for alert in self.active_alerts.values():
                severity = alert.severity.value
                severity_counts[severity] = severity_counts.get(
                    severity, 0) + 1

            return {
                'total_rules': total_rules,
                'enabled_rules': enabled_rules,
                'active_alerts': active_alerts,
                'total_channels': len(self.channels),
                'severity_counts': severity_counts,
                'monitoring_active': self._monitoring
            }
