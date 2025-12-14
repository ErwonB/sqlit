"""UI navigation mixin for SSMSTUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from textual.widgets import DataTable, Static, TextArea, Tree

if TYPE_CHECKING:
    from ...widgets import VimMode


class UINavigationMixin:
    """Mixin providing UI navigation and vim mode functionality."""

    # These attributes are defined in the main app class
    vim_mode: "VimMode"
    current_connection: Any
    current_config: Any
    _fullscreen_mode: str
    _last_notification: str
    _last_notification_severity: str
    _last_notification_time: str
    _notification_timer: Any
    _notification_history: list

    def _set_fullscreen_mode(self, mode: str) -> None:
        """Set fullscreen mode: none|explorer|query|results."""
        self._fullscreen_mode = mode
        self.screen.remove_class("results-fullscreen")
        self.screen.remove_class("query-fullscreen")
        self.screen.remove_class("explorer-fullscreen")
        if mode == "results":
            self.screen.add_class("results-fullscreen")
        elif mode == "query":
            self.screen.add_class("query-fullscreen")
        elif mode == "explorer":
            self.screen.add_class("explorer-fullscreen")

    def _update_section_labels(self) -> None:
        """Update section labels to highlight the active pane."""
        try:
            label_explorer = self.query_one("#label-explorer", Static)
            label_query = self.query_one("#label-query", Static)
            label_results = self.query_one("#label-results", Static)
        except Exception:
            return

        label_explorer.remove_class("active")
        label_query.remove_class("active")
        label_results.remove_class("active")

        focused = self.focused
        if focused:
            widget = focused
            while widget:
                widget_id = getattr(widget, "id", None)
                if widget_id == "object-tree" or widget_id == "sidebar":
                    label_explorer.add_class("active")
                    break
                elif widget_id == "query-input" or widget_id == "query-area":
                    label_query.add_class("active")
                    break
                elif widget_id == "results-table" or widget_id == "results-area":
                    label_results.add_class("active")
                    break
                widget = getattr(widget, "parent", None)

    def action_focus_explorer(self) -> None:
        """Focus the Object Explorer pane."""
        if self._fullscreen_mode != "none":
            self._set_fullscreen_mode("none")
        self.query_one("#object-tree", Tree).focus()

    def action_focus_query(self) -> None:
        """Focus the Query pane (in NORMAL mode)."""
        from ...widgets import VimMode

        if self._fullscreen_mode != "none":
            self._set_fullscreen_mode("none")
        self.vim_mode = VimMode.NORMAL
        query_input = self.query_one("#query-input", TextArea)
        query_input.read_only = True
        query_input.focus()
        self._update_status_bar()

    def action_focus_results(self) -> None:
        """Focus the Results pane."""
        if self._fullscreen_mode != "none":
            self._set_fullscreen_mode("none")
        self.query_one("#results-table", DataTable).focus()

    def action_enter_insert_mode(self) -> None:
        """Enter INSERT mode for query editing."""
        from ...widgets import VimMode

        query_input = self.query_one("#query-input", TextArea)
        if query_input.has_focus and self.vim_mode == VimMode.NORMAL:
            self.vim_mode = VimMode.INSERT
            query_input.read_only = False
            self._update_status_bar()
            self._update_footer_bindings()

    def action_exit_insert_mode(self) -> None:
        """Exit INSERT mode, return to NORMAL mode."""
        from ...widgets import VimMode

        if self.vim_mode == VimMode.INSERT:
            self.vim_mode = VimMode.NORMAL
            query_input = self.query_one("#query-input", TextArea)
            query_input.read_only = True
            self._hide_autocomplete()
            self._update_status_bar()
            self._update_footer_bindings()

    def _update_status_bar(self) -> None:
        """Update status bar with connection and vim mode info."""
        from ...widgets import VimMode
        from .query import SPINNER_FRAMES

        status = self.query_one("#status-bar", Static)
        conn_info = "Not connected"
        if self.current_config:
            display_info = self.current_config.get_display_info()
            conn_info = f"[#90EE90]Connected to {self.current_config.name}[/] ({display_info})"

        # Build status indicators
        status_parts = []

        # Check if schema is indexing
        if getattr(self, "_schema_indexing", False):
            spinner_idx = getattr(self, "_schema_spinner_index", 0)
            spinner = SPINNER_FRAMES[spinner_idx % len(SPINNER_FRAMES)]
            status_parts.append(f"[bold cyan]{spinner} Indexing...[/]")

        # Check if query is executing
        if getattr(self, "_query_executing", False):
            spinner_idx = getattr(self, "_spinner_index", 0)
            spinner = SPINNER_FRAMES[spinner_idx % len(SPINNER_FRAMES)]
            status_parts.append(f"[bold yellow]{spinner} Running...[/]")

        status_str = "  ".join(status_parts)
        if status_str:
            status_str += "  "

        # Build left side content
        try:
            query_input = self.query_one("#query-input", TextArea)
            if query_input.has_focus:
                if self.vim_mode == VimMode.NORMAL:
                    mode_str = f"[bold orange1]-- {self.vim_mode.value} --[/]"
                else:
                    mode_str = f"[dim]-- {self.vim_mode.value} --[/]"
                left_content = f"{status_str}{mode_str}  {conn_info}"
            else:
                left_content = f"{status_str}{conn_info}"
        except Exception:
            left_content = f"{status_str}{conn_info}"

        notification = getattr(self, "_last_notification", "")
        timestamp = getattr(self, "_last_notification_time", "")
        severity = getattr(self, "_last_notification_severity", "information")

        if notification:
            # Normal/warning notifications on right side
            import re
            left_plain = re.sub(r'\[.*?\]', '', left_content)
            time_prefix = f"[dim]{timestamp}[/] " if timestamp else ""

            if severity == "warning":
                notif_str = f"{time_prefix}[#f0c674]{notification}[/]"
            else:
                notif_str = f"{time_prefix}{notification}"

            notif_plain = f"{timestamp} {notification}" if timestamp else notification

            try:
                total_width = self.size.width - 2
            except Exception:
                total_width = 80

            gap = total_width - len(left_plain) - len(notif_plain)
            if gap > 2:
                status.update(f"{left_content}{' ' * gap}{notif_str}")
            else:
                status.update(f"{left_content}  {notif_str}")
        else:
            status.update(left_content)

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: str = "information",
        timeout: float = 3.0,
    ) -> None:
        """Show notification in status bar (takes over full bar temporarily).

        Args:
            message: The notification message.
            title: Ignored (for API compatibility).
            severity: One of "information", "warning", "error".
            timeout: Seconds before auto-clearing (default 3s, errors stay 5s).
        """
        from datetime import datetime

        # Cancel any existing timer
        if hasattr(self, "_notification_timer") and self._notification_timer is not None:
            self._notification_timer.stop()
            self._notification_timer = None

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._notification_history.append((timestamp, message, severity))

        if severity == "error":
            # Clear any status bar notification and show error as dialog
            self._last_notification = ""
            self._last_notification_severity = "information"
            self._last_notification_time = ""
            self._update_status_bar()
            from ..screens import ErrorScreen
            self.push_screen(ErrorScreen(message, timestamp))
        else:
            # Show normal/warning in status bar
            self._last_notification = message
            self._last_notification_severity = severity
            self._last_notification_time = timestamp
            self._update_status_bar()

    def action_show_notifications(self) -> None:
        """Show the notification history dialog."""
        from ..screens import NotificationHistoryScreen

        self.push_screen(NotificationHistoryScreen(self._notification_history))

    def action_dismiss_notification(self) -> None:
        """Dismiss the current notification."""
        if self._last_notification:
            self._last_notification = ""
            self._last_notification_severity = "information"
            self._last_notification_time = ""
            self._update_status_bar()

    def action_toggle_fullscreen(self) -> None:
        """Toggle fullscreen for the currently focused pane."""
        try:
            tree = self.query_one("#object-tree", Tree)
            query_input = self.query_one("#query-input", TextArea)
            results_table = self.query_one("#results-table", DataTable)
        except Exception:
            return

        if tree.has_focus:
            target = "explorer"
        elif query_input.has_focus:
            target = "query"
        elif results_table.has_focus:
            target = "results"
        else:
            target = "none"

        if target != "none" and self._fullscreen_mode == target:
            self._set_fullscreen_mode("none")
        else:
            self._set_fullscreen_mode(target)

        if self._fullscreen_mode == "explorer":
            tree.focus()
        elif self._fullscreen_mode == "query":
            query_input.focus()
        elif self._fullscreen_mode == "results":
            results_table.focus()

        self._update_section_labels()
        self._update_footer_bindings()

    def _update_footer_bindings(self) -> None:
        """Update footer with context-appropriate bindings."""
        from ...widgets import ContextFooter, KeyBinding, VimMode

        # Don't update if a modal screen is open
        if len(self.screen_stack) > 1:
            return

        try:
            footer = self.query_one(ContextFooter)
            tree = self.query_one("#object-tree", Tree)
            query_input = self.query_one("#query-input", TextArea)
            results_table = self.query_one("#results-table", DataTable)
        except Exception:
            return

        left_bindings: list[KeyBinding] = []

        if tree.has_focus:
            node = tree.cursor_node
            node_type = None
            is_root = node == tree.root if node else False

            if node and node.data:
                node_type = node.data[0]

            if is_root or node_type is None:
                left_bindings.append(KeyBinding("n", "New Connection", "new_connection"))
                left_bindings.append(KeyBinding("R", "Refresh", "refresh_tree"))
                left_bindings.append(KeyBinding("f", "Fullscreen", "toggle_fullscreen"))

            elif node_type == "connection":
                config = node.data[1] if node and node.data else None
                is_current = self.current_config and config and config.name == self.current_config.name
                if is_current and self.current_connection:
                    left_bindings.append(KeyBinding("x", "Disconnect", "disconnect"))
                else:
                    left_bindings.append(KeyBinding("enter", "Connect", "connect_selected"))
                left_bindings.append(KeyBinding("n", "New", "new_connection"))
                left_bindings.append(KeyBinding("e", "Edit", "edit_connection"))
                left_bindings.append(KeyBinding("d", "Delete", "delete_connection"))
                left_bindings.append(KeyBinding("R", "Refresh", "refresh_tree"))
                left_bindings.append(KeyBinding("f", "Fullscreen", "toggle_fullscreen"))

            elif node_type in ("table", "view"):
                left_bindings.append(KeyBinding("enter", "Columns", "toggle_node"))
                left_bindings.append(KeyBinding("s", "Select TOP 100", "select_table"))
                left_bindings.append(KeyBinding("R", "Refresh", "refresh_tree"))
                left_bindings.append(KeyBinding("f", "Fullscreen", "toggle_fullscreen"))

            elif node_type == "database":
                left_bindings.append(KeyBinding("enter", "Expand", "toggle_node"))
                left_bindings.append(KeyBinding("R", "Refresh", "refresh_tree"))
                left_bindings.append(KeyBinding("f", "Fullscreen", "toggle_fullscreen"))

            elif node_type == "folder":
                left_bindings.append(KeyBinding("enter", "Expand", "toggle_node"))
                left_bindings.append(KeyBinding("R", "Refresh", "refresh_tree"))
                left_bindings.append(KeyBinding("f", "Fullscreen", "toggle_fullscreen"))

        elif query_input.has_focus:
            if self.vim_mode == VimMode.NORMAL:
                left_bindings.append(KeyBinding("i", "Insert Mode", "enter_insert_mode"))
                if self.current_connection:
                    left_bindings.append(KeyBinding("enter", "Execute", "execute_query"))
                    left_bindings.append(KeyBinding("h", "History", "show_history"))
                left_bindings.append(KeyBinding("d", "Clear", "clear_query"))
                left_bindings.append(KeyBinding("n", "New", "new_query"))
                left_bindings.append(KeyBinding("f", "Fullscreen", "toggle_fullscreen"))
            else:
                left_bindings.append(KeyBinding("esc", "Normal Mode", "exit_insert_mode"))
                if self.current_connection:
                    left_bindings.append(KeyBinding("f5", "Execute", "execute_query_insert"))
                left_bindings.append(KeyBinding("tab", "Autocomplete", "autocomplete_accept"))

        elif results_table.has_focus:
            if self.current_connection:
                left_bindings.append(KeyBinding("enter", "Re-run", "execute_query"))
                left_bindings.append(KeyBinding("f", "Fullscreen", "toggle_fullscreen"))
                left_bindings.append(KeyBinding("v", "View cell", "view_cell"))
                left_bindings.append(KeyBinding("y", "Copy cell", "copy_cell"))
                left_bindings.append(KeyBinding("Y", "Copy row", "copy_row"))
                left_bindings.append(KeyBinding("a", "Copy all", "copy_results"))

        right_bindings: list[KeyBinding] = []
        if self.vim_mode != VimMode.INSERT:
            right_bindings.extend(
                [
                    KeyBinding("?", "Help", "show_help"),
                    KeyBinding("^p", "Commands", "command_palette"),
                    KeyBinding("^q", "Quit", "quit"),
                ]
            )
        else:
            right_bindings.append(KeyBinding("^q", "Quit", "quit"))

        footer.set_bindings(left_bindings, right_bindings)

    def action_show_help(self) -> None:
        """Show help with all keybindings."""
        from ..screens import HelpScreen

        help_text = """
[bold]Object Explorer:[/]
  enter    Connect/Expand/Columns
  s        Select TOP 100 (table/view)
  n        New connection
  e        Edit connection
  d        Delete connection
  R        Refresh
  f        Fullscreen explorer
  z        Collapse all
  x        Disconnect

[bold]Query Editor (Vim Mode):[/]
  i        Enter INSERT mode
  esc      Exit to NORMAL mode
  enter    Execute query (NORMAL)
  f5       Execute query (stay INSERT)
  h        Query history
  d        Clear query
  n        New query (clear all)
  tab      Accept autocomplete (INSERT)
  f        Fullscreen query

[bold]Panes (NORMAL mode):[/]
  e        Object Explorer
  q        Query
  r        Results

[bold]Results:[/]
  f        Fullscreen results
  v        View selected cell
  y        Copy selected cell
  Y        Copy selected row
  a        Copy all results

[bold]General:[/]
  ?        Show this help
  ^p       Command palette
  ^q       Quit
  (Cmd)    Test connections (Ctrl+P)
"""
        self.push_screen(HelpScreen(help_text))

    def on_descendant_focus(self, event) -> None:
        """Handle focus changes to update section labels and footer."""
        from ...widgets import VimMode

        self._update_section_labels()
        try:
            query_input = self.query_one("#query-input", TextArea)
            if not query_input.has_focus and self.vim_mode == VimMode.INSERT:
                self.vim_mode = VimMode.NORMAL
                query_input.read_only = True
        except Exception:
            pass
        self._update_footer_bindings()
        self._update_status_bar()

    def on_descendant_blur(self, event) -> None:
        """Handle blur to update section labels."""
        self.call_later(self._update_section_labels)
