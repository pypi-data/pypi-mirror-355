"""
Real-time alerting system for DataLineagePy.

This module provides:
- Real-time monitoring of lineage operations
- Configurable alert rules and thresholds
- Multiple notification channels (email, Slack, webhooks)
- Performance and quality alerts
- Anomaly detection alerts
"""

from .alert_manager import AlertManager, AlertRule, AlertSeverity
from .monitors import (
    PerformanceMonitor,
    QualityMonitor,
    AnomalyMonitor,
    LineageMonitor
)
from .channels import (
    EmailChannel,
    SlackChannel,
    WebhookChannel,
    ConsoleChannel
)
from .rules import (
    PerformanceRule,
    QualityRule,
    AnomalyRule,
    CustomRule
)

__all__ = [
    # Core alerting
    'AlertManager',
    'AlertRule',
    'AlertSeverity',

    # Monitors
    'PerformanceMonitor',
    'QualityMonitor',
    'AnomalyMonitor',
    'LineageMonitor',

    # Notification channels
    'EmailChannel',
    'SlackChannel',
    'WebhookChannel',
    'ConsoleChannel',

    # Alert rules
    'PerformanceRule',
    'QualityRule',
    'AnomalyRule',
    'CustomRule',
]
