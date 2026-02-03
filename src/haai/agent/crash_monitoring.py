"""
Crash Monitoring Integration

Integrates crash detection and alerting with HAAI agents.
Provides seamless integration for monitoring agent health.
"""

import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from ..core.logging import CrashDetectionLogger, get_app_logger
from ..core.exception_handler import GlobalExceptionHandler, ExceptionGuard
from ..core.alert_dispatcher import AlertDispatcher, Alert, AlertSeverity, AlertChannel, AlertConfig


@dataclass
class CrashMonitorConfig:
    """Configuration for crash monitoring."""
    # Enable/disable features
    enable_global_handler: bool = True
    enable_alerts: bool = True
    enable_health_endpoint: bool = True
    
    # Alert configuration
    alert_config: AlertConfig = field(default_factory=AlertConfig)
    
    # Integration settings
    log_file: str = "logs/crash_monitor.log"
    crash_history_limit: int = 100
    
    # Fail fast mode (re-raise exceptions after logging)
    fail_fast: bool = False


class CrashMonitor:
    """
    Crash monitoring system for HAAI agents.
    
    Features:
    - Global exception handling
    - Structured crash logging
    - Multi-channel alerting
    - Health statistics tracking
    - Agent lifecycle integration
    """
    
    def __init__(self, agent_id: str, config: CrashMonitorConfig = None):
        """
        Initialize the crash monitor.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Optional configuration
        """
        self.agent_id = agent_id
        self.config = config or CrashMonitorConfig()
        
        # Initialize logger
        self.logger = CrashDetectionLogger(
            f"haai.crash_monitor.{agent_id}",
            log_file=self.config.log_file
        )
        
        # Initialize exception handler
        self.exception_handler = GlobalExceptionHandler(
            self.logger,
            fail_fast=self.config.fail_fast
        )
        
        # Initialize alert dispatcher
        self.alert_dispatcher = AlertDispatcher(self.config.alert_config)
        
        # State tracking
        self.is_monitoring = False
        self.crash_count = 0
        self.start_time: Optional[datetime] = None
        self.last_crash_time: Optional[datetime] = None
        
        # Register with app logger
        app_logger = get_app_logger()
        app_logger.log_info_with_context(
            f"CrashMonitor initialized for agent {agent_id}",
            {"agent_id": agent_id}
        )
    
    def start(self) -> None:
        """Start crash monitoring."""
        if self.is_monitoring:
            self.logger.logger.warning("Crash monitoring already started")
            return
        
        self.start_time = datetime.now()
        self.is_monitoring = True
        
        # Install global exception handler
        if self.config.enable_global_handler:
            self.exception_handler.install()
            self.logger.logger.info("Global exception handler installed")
        
        # Log startup
        self.logger.logger.info(f"Crash monitoring started for agent {self.agent_id}")
    
    def stop(self) -> None:
        """Stop crash monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        # Uninstall exception handler
        if self.config.enable_global_handler:
            self.exception_handler.uninstall()
        
        # Log shutdown
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        self.logger.logger.info(
            f"Crash monitoring stopped for agent {self.agent_id} "
            f"(uptime: {uptime:.1f}s, crashes: {self.crash_count})"
        )
    
    def register_with_agent(self, agent) -> None:
        """
        Register crash monitor with a HAAI agent.
        
        Args:
            agent: HAAI agent instance
        """
        # Add crash monitoring to agent state
        agent.state.crash_monitor = self
        
        # Log registration
        self.logger.log_info_with_context(
            f"CrashMonitor registered with agent",
            {"agent_id": self.agent_id, "has_agent": True}
        )
    
    def on_crash(self, crash_id: str, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Handle a detected crash.
        
        Args:
            crash_id: Unique crash identifier
            error: The exception that occurred
            context: Additional context information
        """
        self.crash_count += 1
        self.last_crash_time = datetime.now()
        
        # Build crash data
        crash_data = {
            "crash_id": crash_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "agent_id": self.agent_id,
            "context": context or {},
            "timestamp": self.last_crash_time.isoformat()
        }
        
        # Dispatch alerts
        if self.config.enable_alerts:
            try:
                self.alert_dispatcher.dispatch_crash_alert(crash_data)
            except Exception as e:
                self.logger.logger.error(f"Failed to dispatch crash alert: {e}")
        
        # Update agent state if available
        if hasattr(self, 'agent') and self.agent:
            self.agent.state.error_log.append(
                f"CRASH|{crash_id}|{type(error).__name__}|{datetime.now().isoformat()}"
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health status.
        
        Returns:
            Health status dictionary
        """
        now = datetime.now()
        uptime = (now - self.start_time).total_seconds() if self.start_time else 0
        
        # Calculate crash rate (crashes per hour)
        hours_running = uptime / 3600
        crash_rate = (self.crash_count / hours_running) if hours_running > 0 else 0
        
        return {
            "agent_id": self.agent_id,
            "is_monitoring": self.is_monitoring,
            "uptime_seconds": uptime,
            "crash_count": self.crash_count,
            "crash_rate_per_hour": crash_rate,
            "last_crash_time": self.last_crash_time.isoformat() if self.last_crash_time else None,
            "status": "healthy" if self.crash_count == 0 else ("degraded" if self.crash_count < 5 else "critical"),
            "timestamp": now.isoformat()
        }
    
    def get_crash_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent crash history.
        
        Args:
            limit: Maximum number of crashes to return
            
        Returns:
            List of crash records
        """
        return self.logger.get_crash_history(limit)
    
    def clear_crash_history(self) -> None:
        """Clear the in-memory crash history."""
        self.logger.clear_crash_history()
        self.crash_count = 0
    
    def guard(self, context: Dict[str, Any] = None) -> ExceptionGuard:
        """
        Create an exception guard context manager.
        
        Usage:
            with crash_monitor.guard({"operation": "process_data"}):
                # Code that might crash
                pass
            
            if guard.crash_id:
                # Handle the crash
                pass
        
        Args:
            context: Additional context for crash logs
            
        Returns:
            ExceptionGuard context manager
        """
        return ExceptionGuard(
            logger=self.logger,
            context={"agent_id": self.agent_id, **(context or {})},
            reraise=self.config.fail_fast
        )


def create_crash_monitor(agent_id: str, 
                         enable_email_alerts: bool = False,
                         enable_webhook_alerts: bool = False,
                         webhook_url: str = "",
                         enable_slack_alerts: bool = False,
                         slack_webhook: str = "") -> CrashMonitor:
    """
    Factory function to create a configured crash monitor.
    
    Args:
        agent_id: Unique agent identifier
        enable_email_alerts: Enable email notifications
        enable_webhook_alerts: Enable webhook notifications
        webhook_url: Webhook endpoint URL
        enable_slack_alerts: Enable Slack notifications
        slack_webhook: Slack webhook URL
        
    Returns:
        Configured CrashMonitor instance
    """
    # Build alert config
    alert_config = AlertConfig(
        email_enabled=enable_email_alerts,
        webhook_enabled=enable_webhook_alerts,
        webhook_url=webhook_url,
        slack_enabled=enable_slack_alerts,
        slack_webhook_url=slack_webhook
    )
    
    config = CrashMonitorConfig(
        enable_alerts=True,
        alert_config=alert_config
    )
    
    return CrashMonitor(agent_id, config)


# Integration with existing agent code
def install_crash_monitoring(agent, 
                            enable_alerts: bool = False,
                            webhook_url: str = "") -> CrashMonitor:
    """
    Install crash monitoring for an existing agent.
    
    Args:
        agent: HAAI agent instance
        enable_alerts: Enable alert dispatch
        webhook_url: Optional webhook URL for alerts
        
    Returns:
        Configured CrashMonitor instance
    """
    monitor = create_crash_monitor(
        agent_id=agent.agent_id,
        enable_webhook_alerts=enable_alerts,
        webhook_url=webhook_url
    )
    
    monitor.register_with_agent(agent)
    monitor.start()
    
    return monitor
