"""Tests for schema capability functions."""

from sqlit.db.schema import (
    get_default_port,
    get_display_name,
    has_advanced_auth,
    is_file_based,
    supports_ssh,
)


class TestIsFileBased:
    def test_unknown_type_returns_false(self):
        assert is_file_based("nonexistent") is False


class TestHasAdvancedAuth:
    def test_unknown_type_returns_false(self):
        assert has_advanced_auth("nonexistent") is False


class TestSupportsSSH:
    def test_unknown_type_returns_false(self):
        assert supports_ssh("nonexistent") is False


class TestGetDefaultPort:
    def test_unknown_type_returns_fallback(self):
        assert get_default_port("nonexistent") == "1433"


class TestGetDisplayName:
    def test_unknown_type_returns_input(self):
        assert get_display_name("nonexistent") == "nonexistent"
