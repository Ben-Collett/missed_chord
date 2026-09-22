import pytest
from logging_modes import LoggingMode


class TestLoggingMode:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("load", LoggingMode.LOAD),
            ("overwrite", LoggingMode.OVERWRITE),
            ("increment", LoggingMode.INCREMENT),
        ],
    )
    def test_parse_valid(self, value, expected):
        assert LoggingMode.parse(value) == expected

    @pytest.mark.parametrize(
        "value",
        ["", "invalid", "LOAD", "load ", "append"],
    )
    def test_parse_invalid_defaults_to_load(self, value):
        assert LoggingMode.parse(value) == LoggingMode.LOAD
