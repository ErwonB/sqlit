"""Notification history screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from ...widgets import Dialog


class NotificationHistoryScreen(ModalScreen):
    """Modal screen for viewing notification history."""

    BINDINGS = [
        Binding("escape", "cancel", "Close"),
        Binding("q", "cancel", "Close"),
    ]

    CSS = """
    NotificationHistoryScreen {
        align: center middle;
        background: transparent;
    }

    #notifications-dialog {
        width: 90;
        max-width: 90%;
        height: 80%;
        max-height: 90%;
    }

    #notifications-scroll {
        height: 1fr;
        background: $surface;
        border: none;
        padding: 1;
    }

    #notifications-empty {
        text-align: center;
        color: $text-muted;
        padding: 2;
    }

    .notification-item {
        padding: 0 1;
        margin-bottom: 0;
    }

    .notification-error {
        color: #ff6b6b;
    }

    .notification-warning {
        color: #f0c674;
    }

    .notification-info {
        color: $text;
    }
    """

    def __init__(self, notifications: list[tuple[str, str, str]]):
        """Initialize with notification history.

        Args:
            notifications: List of (timestamp, message, severity) tuples.
        """
        super().__init__()
        self.notifications = notifications

    def compose(self) -> ComposeResult:
        shortcuts = [("Close", "Esc")]

        with Dialog(id="notifications-dialog", title="Notifications", shortcuts=shortcuts):
            with VerticalScroll(id="notifications-scroll"):
                if self.notifications:
                    for timestamp, message, severity in reversed(self.notifications):
                        if severity == "error":
                            color_class = "notification-error"
                        elif severity == "warning":
                            color_class = "notification-warning"
                        else:
                            color_class = "notification-info"

                        yield Static(
                            f"[dim]{timestamp}[/] {message}",
                            classes=f"notification-item {color_class}",
                        )
                else:
                    yield Static("No notifications yet", id="notifications-empty")

    def on_mount(self) -> None:
        scroll = self.query_one("#notifications-scroll", VerticalScroll)
        scroll.focus()

    def action_cancel(self) -> None:
        self.dismiss(None)
