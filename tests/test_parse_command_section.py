import pytest
from parse_command_section import parse_command_section


class TestParseCommandSection:
    @pytest.mark.parametrize(
        ("config", "expected"),
        [
            (
                {"commands": {"RL": ["reload_config"]}},
                {"RL": ["reload_config"]},
            ),
            (
                {"commands": {"CB": ["clear_buffer"]}},
                {"CB": ["clear_buffer"]},
            ),
            (
                {"commands": {"RL": ["reload_config"], "CB": ["clear_buffer"]}},
                {"RL": ["reload_config"], "CB": ["clear_buffer"]},
            ),
            (
                {"commands": {"AA": ["action_a"], "BB": ["action_b"]}},
                {"AA": ["action_a"], "BB": ["action_b"]},
            ),
        ],
    )
    def test_parse_with_commands(self, config, expected):
        assert parse_command_section(config) == expected

    @pytest.mark.parametrize(
        "config",
        [
            {},
            {"other": "stuff"},
            {"commands": None},
            {"not_commands": {"RL": ["reload_config"]}},
        ],
    )
    def test_parse_missing_or_none_commands_returns_default(self, config):
        expected = {"RL": ["reload_config"], "CB": ["clear_buffer"]}
        assert parse_command_section(config) == expected
