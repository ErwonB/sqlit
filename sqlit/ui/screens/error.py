"""Error dialog screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

from ...widgets import Dialog


class ErrorScreen(ModalScreen):
    """Modal screen for displaying error messages."""

    BINDINGS = [
        Binding("escape", "dismiss_error", "Close"),
        Binding("enter", "dismiss_error", "Close"),
        Binding("d", "dismiss_error", "Close"),
    ]

    CSS = """
    ErrorScreen {
        align: center middle;
        background: transparent;
    }

    #error-dialog {
        width: 60;
        max-width: 90%;
        border: solid #ff6b6b;
        border-subtitle-color: #ff6b6b;
    }

    #error-dialog > Container {
        border: none;
    }

    #error-message {
        padding: 1 2;
        color: #ff6b6b;
    }

    #error-timestamp {
        padding: 0 2 1 2;
        color: $text-muted;
    }
    """

    def __init__(self, message: str, timestamp: str = ""):
        super().__init__()
        self.message = message
        self.timestamp = timestamp

    def compose(self) -> ComposeResult:
        shortcuts = [("Close", "Enter")]
        with Dialog(id="error-dialog", title="Error", shortcuts=shortcuts):
            if self.timestamp:
                yield Static(self.timestamp, id="error-timestamp")
            yield Static(self.message, id="error-message")

    def action_dismiss_error(self) -> None:
        self.dismiss(None)
