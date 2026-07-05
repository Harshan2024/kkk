"""
notifier.py — CarbonTracker Alert & Notification Abstraction Layer
===================================================================
Phase 11: Alert Readiness Infrastructure

This module provides a pluggable notification abstraction. All notification
channels (Email, Slack, Discord, Teams) are stubs that can be activated
by configuring environment variables and uncommenting adapter code.

Usage:
    from app.utils.notifier import send_notification, NotificationEvent, NotificationLevel

    event = NotificationEvent(
        level=NotificationLevel.ERROR,
        title="Database Connection Failed",
        message="PostgreSQL connection dropped after 3 retries.",
        context={"endpoint": "/api/v1/activities", "retry_count": 3}
    )
    send_notification(event)
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional

logger = logging.getLogger("carbontracker.notifier")


# ─── Notification Levels ──────────────────────────────────────────────────────
class NotificationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Emoji traffic-light indicators for each level
LEVEL_EMOJI = {
    NotificationLevel.INFO: "🔵",
    NotificationLevel.WARNING: "🟡",
    NotificationLevel.ERROR: "🔴",
    NotificationLevel.CRITICAL: "🚨",
}


# ─── Event Dataclass ──────────────────────────────────────────────────────────
@dataclass
class NotificationEvent:
    """Represents a single alert notification event."""
    level: NotificationLevel
    title: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "carbontracker-ai"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "context": self.context,
            "source": self.source,
            "timestamp": self.timestamp,
        }

    def format_text(self) -> str:
        emoji = LEVEL_EMOJI.get(self.level, "ℹ️")
        ctx_str = "\n".join(f"  {k}: {v}" for k, v in self.context.items()) if self.context else "  (none)"
        return (
            f"{emoji} [{self.level.value.upper()}] {self.title}\n"
            f"Source: {self.source} | {self.timestamp}\n"
            f"Message: {self.message}\n"
            f"Context:\n{ctx_str}"
        )


# ─── Notification Channel Base ───────────────────────────────────────────────
class NotificationChannel:
    """Abstract base for notification adapters."""
    name: str = "base"

    def is_configured(self) -> bool:
        return False

    def send(self, event: NotificationEvent) -> bool:
        """Send a notification. Returns True on success."""
        return False


# ─── Log Channel (always active) ─────────────────────────────────────────────
class LogChannel(NotificationChannel):
    """Logs notifications to the structured application log. Always active."""
    name = "log"

    def is_configured(self) -> bool:
        return True

    def send(self, event: NotificationEvent) -> bool:
        level_map = {
            NotificationLevel.INFO: logger.info,
            NotificationLevel.WARNING: logger.warning,
            NotificationLevel.ERROR: logger.error,
            NotificationLevel.CRITICAL: logger.critical,
        }
        log_fn = level_map.get(event.level, logger.info)
        log_fn(
            f"[NOTIFICATION] {event.title}: {event.message} | context={event.context}"
        )
        return True


# ─── Email Channel (stub) ────────────────────────────────────────────────────
class EmailChannel(NotificationChannel):
    """
    Email notification adapter (stub).

    To activate:
    1. Set environment variables:
       ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
       ALERT_EMAIL_SMTP_PORT=587
       ALERT_EMAIL_FROM=alerts@yourdomain.com
       ALERT_EMAIL_TO=oncall@yourdomain.com
       ALERT_EMAIL_PASSWORD=<app-password>
    2. Uncomment the smtplib send logic below.
    """
    name = "email"

    def is_configured(self) -> bool:
        return bool(
            os.getenv("ALERT_EMAIL_SMTP_HOST")
            and os.getenv("ALERT_EMAIL_FROM")
            and os.getenv("ALERT_EMAIL_TO")
        )

    def send(self, event: NotificationEvent) -> bool:
        if not self.is_configured():
            return False
        # --- STUB: Uncomment to activate ---
        # import smtplib
        # from email.mime.text import MIMEText
        # msg = MIMEText(event.format_text())
        # msg["Subject"] = f"[CarbonTracker] {event.level.upper()}: {event.title}"
        # msg["From"] = os.getenv("ALERT_EMAIL_FROM")
        # msg["To"] = os.getenv("ALERT_EMAIL_TO")
        # with smtplib.SMTP(os.getenv("ALERT_EMAIL_SMTP_HOST"), int(os.getenv("ALERT_EMAIL_SMTP_PORT", 587))) as s:
        #     s.starttls()
        #     s.login(os.getenv("ALERT_EMAIL_FROM"), os.getenv("ALERT_EMAIL_PASSWORD"))
        #     s.send_message(msg)
        logger.info(f"[EmailChannel STUB] Would send: {event.title}")
        return True


# ─── Slack Channel (stub) ────────────────────────────────────────────────────
class SlackChannel(NotificationChannel):
    """
    Slack notification adapter (stub).

    To activate:
    1. Create an Incoming Webhook at https://api.slack.com/messaging/webhooks
    2. Set: ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
    3. Uncomment the requests.post logic below.
    """
    name = "slack"

    def is_configured(self) -> bool:
        return bool(os.getenv("ALERT_SLACK_WEBHOOK_URL"))

    def send(self, event: NotificationEvent) -> bool:
        if not self.is_configured():
            return False
        # --- STUB: Uncomment to activate ---
        # import requests
        # payload = {
        #     "text": event.format_text(),
        #     "username": "CarbonTracker Alerts",
        #     "icon_emoji": ":earth_africa:",
        # }
        # resp = requests.post(os.getenv("ALERT_SLACK_WEBHOOK_URL"), json=payload, timeout=5)
        # return resp.status_code == 200
        logger.info(f"[SlackChannel STUB] Would send: {event.title}")
        return True


# ─── Discord Channel (stub) ──────────────────────────────────────────────────
class DiscordChannel(NotificationChannel):
    """
    Discord notification adapter (stub).

    To activate:
    1. Create a Webhook in your Discord server channel settings.
    2. Set: ALERT_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
    3. Uncomment the requests.post logic below.
    """
    name = "discord"

    def is_configured(self) -> bool:
        return bool(os.getenv("ALERT_DISCORD_WEBHOOK_URL"))

    def send(self, event: NotificationEvent) -> bool:
        if not self.is_configured():
            return False
        # --- STUB: Uncomment to activate ---
        # import requests
        # payload = {"content": event.format_text()[:2000]}
        # resp = requests.post(os.getenv("ALERT_DISCORD_WEBHOOK_URL"), json=payload, timeout=5)
        # return resp.status_code in (200, 204)
        logger.info(f"[DiscordChannel STUB] Would send: {event.title}")
        return True


# ─── Microsoft Teams Channel (stub) ─────────────────────────────────────────
class TeamsChannel(NotificationChannel):
    """
    Microsoft Teams notification adapter (stub).

    To activate:
    1. Create an Incoming Webhook connector in your Teams channel.
    2. Set: ALERT_TEAMS_WEBHOOK_URL=https://...webhook.office.com/...
    3. Uncomment the requests.post logic below.
    """
    name = "teams"

    def is_configured(self) -> bool:
        return bool(os.getenv("ALERT_TEAMS_WEBHOOK_URL"))

    def send(self, event: NotificationEvent) -> bool:
        if not self.is_configured():
            return False
        # --- STUB: Uncomment to activate ---
        # import requests
        # payload = {
        #     "@type": "MessageCard",
        #     "@context": "http://schema.org/extensions",
        #     "themeColor": "FF0000" if event.level == NotificationLevel.CRITICAL else "FFA500",
        #     "summary": event.title,
        #     "sections": [{"activityTitle": event.title, "activityText": event.format_text()}]
        # }
        # resp = requests.post(os.getenv("ALERT_TEAMS_WEBHOOK_URL"), json=payload, timeout=5)
        # return resp.status_code == 200
        logger.info(f"[TeamsChannel STUB] Would send: {event.title}")
        return True


# ─── Notification Router ──────────────────────────────────────────────────────
class NotificationRouter:
    """
    Routes notification events to all configured channels.
    The LogChannel is always active. Others activate via environment variables.
    """

    def __init__(self):
        self._channels: List[NotificationChannel] = [
            LogChannel(),
            EmailChannel(),
            SlackChannel(),
            DiscordChannel(),
            TeamsChannel(),
        ]
        # Minimum level required to trigger external notifications
        self._min_external_level = NotificationLevel(
            os.getenv("ALERT_MIN_LEVEL", NotificationLevel.ERROR.value)
        )

    def dispatch(self, event: NotificationEvent) -> Dict[str, bool]:
        """Send event to all configured channels. Returns per-channel result."""
        results: Dict[str, bool] = {}
        level_order = [
            NotificationLevel.INFO,
            NotificationLevel.WARNING,
            NotificationLevel.ERROR,
            NotificationLevel.CRITICAL,
        ]

        for channel in self._channels:
            if not channel.is_configured():
                continue
            # LogChannel always fires; external channels respect min level
            if channel.name != "log":
                if level_order.index(event.level) < level_order.index(self._min_external_level):
                    results[channel.name] = False
                    continue
            try:
                results[channel.name] = channel.send(event)
            except Exception as e:
                logger.error(f"[NotificationRouter] Channel {channel.name} failed: {e}")
                results[channel.name] = False

        return results

    def configured_channels(self) -> List[str]:
        return [c.name for c in self._channels if c.is_configured()]


# ── Global router singleton ───────────────────────────────────────────────────
_router = NotificationRouter()


def send_notification(event: NotificationEvent) -> Dict[str, bool]:
    """
    Public API: Send a notification event to all configured channels.

    Args:
        event: A NotificationEvent describing the alert.

    Returns:
        Dict mapping channel names to success booleans.
    """
    return _router.dispatch(event)


def notify_error(title: str, message: str, context: Optional[Dict] = None) -> None:
    """Shorthand for sending an ERROR notification."""
    send_notification(NotificationEvent(
        level=NotificationLevel.ERROR,
        title=title,
        message=message,
        context=context or {}
    ))


def notify_critical(title: str, message: str, context: Optional[Dict] = None) -> None:
    """Shorthand for sending a CRITICAL notification."""
    send_notification(NotificationEvent(
        level=NotificationLevel.CRITICAL,
        title=title,
        message=message,
        context=context or {}
    ))


def notify_warning(title: str, message: str, context: Optional[Dict] = None) -> None:
    """Shorthand for sending a WARNING notification."""
    send_notification(NotificationEvent(
        level=NotificationLevel.WARNING,
        title=title,
        message=message,
        context=context or {}
    ))


def get_notification_status() -> dict:
    """Returns the current state of all notification channels."""
    return {
        "configured_channels": _router.configured_channels(),
        "min_external_level": _router._min_external_level.value,
        "channels": {
            c.name: c.is_configured()
            for c in _router._channels
        }
    }
