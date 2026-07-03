import pytest
from unittest.mock import patch
from notification_modes import NotificationMode


class TestNotificationMode:
    def test_enum_values(self):
        assert NotificationMode.QT.value == "qt"
        assert NotificationMode.NOTIFY.value == "notify"

    @pytest.mark.parametrize(
        ("mode", "expected"),
        [
            ("qt", NotificationMode.QT),
            ("notify", NotificationMode.NOTIFY),
        ],
    )
    def test_parse_explicit(self, mode, expected):
        assert NotificationMode.parse(mode) == expected

    @patch("notification_modes.is_on_linux", return_value=True)
    def test_parse_auto_on_linux(self, mock_is_linux):
        assert NotificationMode.parse("auto") == NotificationMode.NOTIFY

    @patch("notification_modes.is_on_linux", return_value=False)
    def test_parse_auto_on_non_linux(self, mock_is_linux):
        assert NotificationMode.parse("auto") == NotificationMode.QT

    @patch("notification_modes.is_on_linux", return_value=True)
    def test_parse_invalid_defaults_to_auto_linux(self, mock_is_linux):
        assert NotificationMode.parse("bad") == NotificationMode.NOTIFY

    @patch("notification_modes.is_on_linux", return_value=False)
    def test_parse_invalid_defaults_to_auto_non_linux(self, mock_is_linux):
        assert NotificationMode.parse("bad") == NotificationMode.QT
