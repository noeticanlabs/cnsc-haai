"""
Alert Dispatcher

Dispatches crash alerts via multiple channels:
- Email (SMTP)
- Webhooks (HTTP POST)
- Slack (Incoming Webhook)

Includes rate limiting to prevent alert spam.
"""

import smtplib
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Try to import optional dependencies
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Available alert channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    CONSOLE = "console"


@dataclass
class AlertConfig:
    """Configuration for alert dispatching."""
    # Email settings
    email_enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = "haai-alerts@example.com"
    email_to: List[str] = field(default_factory=list)
    
    # Webhook settings
    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)
    
    # Slack settings
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # Rate limiting
    rate_limit_window_minutes: int = 5
    max_alerts_per_window: int = 5
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: int = 5


@dataclass
class Alert:
    """Alert to be dispatched."""
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    crash_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    channels: List[AlertChannel] = field(default_factory=list)


class AlertDispatcher:
    """
    Dispatches alerts to multiple channels with rate limiting.
    
    Features:
    - Multi-channel alert dispatch (email, webhook, slack)
    - Rate limiting to prevent spam
    - Retry logic for failed dispatches
    - Thread-safe operation
    """
    
    def __init__(self, config: AlertConfig = None):
        """
        Initialize the alert dispatcher.
        
        Args:
            config: Alert configuration
        """
        self.config = config or AlertConfig()
        self.alert_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        # Rate limiting window
        self.rate_limit_window = timedelta(minutes=self.config.rate_limit_window_minutes)
    
    def dispatch(self, alert: Alert) -> Dict[AlertChannel, bool]:
        """
        Dispatch an alert to configured channels.
        
        Args:
            alert: Alert to dispatch
            
        Returns:
            Dictionary mapping channel to success status
        """
        results = {}
        
        # Check rate limiting
        if not self._check_rate_limit():
            self._log_suppressed_alert(alert)
            return {ch: False for ch in alert.channels}
        
        # Record the alert
        with self._lock:
            self.alert_history.append({
                "alert_id": alert.alert_id,
                "timestamp": datetime.now().isoformat(),
                "severity": alert.severity.value,
                "crash_id": alert.crash_id
            })
        
        # Dispatch to each channel
        for channel in alert.channels:
            success = self._dispatch_to_channel(alert, channel)
            results[channel] = success
        
        return results
    
    def dispatch_crash_alert(self, crash_data: Dict[str, Any]) -> Dict[AlertChannel, bool]:
        """
        Convenience method to dispatch a crash alert.
        
        Args:
            crash_data: Crash information from logger
            
        Returns:
            Dictionary mapping channel to success status
        """
        alert = Alert(
            alert_id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            severity=AlertSeverity.CRITICAL,
            title=f"CRASH DETECTED: {crash_data.get('crash_id', 'UNKNOWN')}",
            message=crash_data.get('error_message', 'Unknown error'),
            crash_id=crash_data.get('crash_id'),
            context=crash_data,
            channels=self._get_default_channels()
        )
        
        return self.dispatch(alert)
    
    def _get_default_channels(self) -> List[AlertChannel]:
        """Get list of enabled channels."""
        channels = []
        if self.config.email_enabled:
            channels.append(AlertChannel.EMAIL)
        if self.config.webhook_enabled:
            channels.append(AlertChannel.WEBHOOK)
        if self.config.slack_enabled:
            channels.append(AlertChannel.SLACK)
        if not channels:
            channels.append(AlertChannel.CONSOLE)
        return channels
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.now()
        cutoff = now - self.rate_limit_window
        
        with self._lock:
            recent_alerts = [
                a for a in self.alert_history
                if datetime.fromisoformat(a["timestamp"]) > cutoff
            ]
            
            return len(recent_alerts) < self.config.max_alerts_per_window
    
    def _dispatch_to_channel(self, alert: Alert, channel: AlertChannel) -> bool:
        """
        Dispatch alert to a specific channel.
        
        Args:
            alert: Alert to dispatch
            channel: Target channel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if channel == AlertChannel.EMAIL:
                return self._send_email(alert)
            elif channel == AlertChannel.WEBHOOK:
                return self._send_webhook(alert)
            elif channel == AlertChannel.SLACK:
                return self._send_slack(alert)
            elif channel == AlertChannel.CONSOLE:
                return self._send_console(alert)
            else:
                return False
        except Exception as e:
            print(f"Failed to dispatch to {channel}: {e}")
            return False
    
    def _send_email(self, alert: Alert) -> bool:
        """Send alert via email."""
        if not self.config.email_enabled or not self.config.email_to:
            return False
        
        try:
            msg = MIMEText(self._format_email_body(alert))
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg["From"] = self.config.email_from
            msg["To"] = ", ".join(self.config.email_to)
            
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_username:
                    server.starttls()
                    server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Email alert failed: {e}")
            return False
    
    def _send_webhook(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        if not self.config.webhook_enabled or not self.config.webhook_url:
            return False
        
        if not AIOHTTP_AVAILABLE:
            print("Webhook alert skipped: aiohttp not installed")
            return False
        
        async def _do_webhook():
            payload = {
                "alert_id": alert.alert_id,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "crash_id": alert.crash_id,
                "context": alert.context,
                "timestamp": alert.timestamp
            }
            
            headers = {"Content-Type": "application/json"}
            headers.update(self.config.webhook_headers)
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.config.webhook_url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        return response.status == 200
            except Exception as e:
                print(f"Webhook alert failed: {e}")
                return False
        
        return asyncio.run(_do_webhook())
    
    def _send_slack(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        if not self.config.slack_enabled or not self.config.slack_webhook_url:
            return False
        
        if not AIOHTTP_AVAILABLE:
            print("Slack alert skipped: aiohttp not installed")
            return False
        
        async def _do_slack():
            payload = {
                "channel": self.config.slack_channel,
                "attachments": [
                    {
                        "color": self._get_slack_color(alert.severity),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Crash ID",
                                "value": alert.crash_id or "N/A",
                                "short": True
                            }
                        ],
                        "footer": "HAAI Crash Detection",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.config.slack_webhook_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        return response.status == 200
            except Exception as e:
                print(f"Slack alert failed: {e}")
                return False
        
        return asyncio.run(_do_slack())
    
    def _send_console(self, alert: Alert) -> bool:
        """Print alert to console."""
        print(f"\n{'='*50}")
        print(f"ALERT: {alert.title}")
        print(f"Severity: {alert.severity.value}")
        print(f"Message: {alert.message}")
        if alert.crash_id:
            print(f"Crash ID: {alert.crash_id}")
        print(f"{'='*50}\n")
        return True
    
    def _format_email_body(self, alert: Alert) -> str:
        """Format alert for email body."""
        return f"""
HAAI Alert Notification
=======================

Alert ID: {alert.alert_id}
Severity: {alert.severity.value.upper()}
Title: {alert.title}
Message: {alert.message}
Crash ID: {alert.crash_id or 'N/A'}
Timestamp: {alert.timestamp}

Context:
{json.dumps(alert.context, indent=2)}

---
Automated alert from HAAI Crash Detection System
"""
    
    def _get_slack_color(self, severity: AlertSeverity) -> str:
        """Get Slack color for severity level."""
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.ERROR: "#ff9900",
            AlertSeverity.CRITICAL: "#ff0000"
        }
        return colors.get(severity, "#808080")
    
    def _log_suppressed_alert(self, alert: Alert) -> None:
        """Log when an alert is suppressed."""
        print(f"Alert suppressed due to rate limiting: {alert.alert_id}")
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent alert history.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent alerts
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            return [
                a for a in self.alert_history
                if datetime.fromisoformat(a["timestamp"]) > cutoff
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert dispatch statistics."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        with self._lock:
            recent = [a for a in self.alert_history 
                     if datetime.fromisoformat(a["timestamp"]) > hour_ago]
            daily = [a for a in self.alert_history 
                    if datetime.fromisoformat(a["timestamp"]) > day_ago]
            
            return {
                "last_hour_count": len(recent),
                "last_24h_count": len(daily),
                "total_count": len(self.alert_history),
                "is_rate_limited": len(recent) >= self.config.max_alerts_per_window
            }


# Convenience function
def create_dispatcher(config_dict: Dict[str, Any] = None) -> AlertDispatcher:
    """
    Create an alert dispatcher from configuration dictionary.
    
    Args:
        config_dict: Configuration dictionary
        
    Returns:
        Configured AlertDispatcher instance
    """
    if config_dict is None:
        config_dict = {}
    
    # Map nested dicts
    if "smtp_config" in config_dict:
        smtp = config_dict.pop("smtp_config")
        config_dict.update({
            "smtp_host": smtp.get("host", "localhost"),
            "smtp_port": smtp.get("port", 587),
            "smtp_username": smtp.get("username", ""),
            "smtp_password": smtp.get("password", ""),
            "email_from": smtp.get("from_addr", "haai-alerts@example.com"),
            "email_to": smtp.get("to_addrs", [])
        })
    
    config = AlertConfig(**config_dict)
    return AlertDispatcher(config)
