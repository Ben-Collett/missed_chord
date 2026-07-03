import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from my_frozen_dict import MyFrozenDict
from chording_modes import ChordingMode
from notification_modes import NotificationMode


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.general.mode = ChordingMode.CHARA_CHORDER
    cfg.notification.mode = NotificationMode.QT
    cfg.notification.message = "$triggers = $chord"
    cfg.filter.blocked = ["bad_chord"]
    cfg.filter.allowed = []
    cfg.commands = {}
    return cfg


@pytest.fixture
def config_wrapper(mock_config):
    patches = [
        patch("config_wrapper.ConfigManager"),
        patch("config_wrapper.DeviceWrapper"),
        patch("config_wrapper.Config", return_value=mock_config),
        patch("config_wrapper._parse_config", return_value={}),
        patch("config_wrapper.ascii_only", return_value={}),
        patch("config_wrapper.load_chords", return_value={}),
        patch("config_wrapper.load_chips", return_value=({}, {})),
        patch("config_wrapper.reverse_dict", return_value={}),
        patch("config_wrapper.flat_inplace_merge_dicts"),
    ]
    for p in patches:
        p.start()
    from config_wrapper import ConfigWrapper
    cw = ConfigWrapper()
    for p in patches:
        p.stop()
    cw.config = mock_config
    return cw


class TestConfigWrapper:
    def test_get_commands_returns_empty_list_for_missing_key(self, config_wrapper):
        assert config_wrapper.get_commands("nonexistent") == []

    def test_get_commands_returns_list(self, config_wrapper):
        from commands import Command
        config_wrapper._commands["test"] = [Command.RELOAD]
        assert config_wrapper.get_commands("test") == [Command.RELOAD]

    def test_has_command_true(self, config_wrapper):
        config_wrapper._commands["exists"] = []
        assert config_wrapper.has_command("exists")

    def test_has_command_false(self, config_wrapper):
        assert not config_wrapper.has_command("missing")

    def test_qt_mode_true(self, config_wrapper):
        config_wrapper.config.notification.mode = NotificationMode.QT
        assert config_wrapper.qt_mode()

    def test_qt_mode_false(self, config_wrapper):
        config_wrapper.config.notification.mode = NotificationMode.NOTIFY
        assert not config_wrapper.qt_mode()

    def test_chara_mode_true(self, config_wrapper):
        config_wrapper.config.general.mode = ChordingMode.CHARA_CHORDER
        assert config_wrapper.chara_mode()

    def test_chara_mode_false(self, config_wrapper):
        config_wrapper.config.general.mode = ChordingMode.FUZZY_CHIPS
        assert not config_wrapper.chara_mode()

    @pytest.mark.parametrize(
        ("trigger", "data_key", "data_val", "expected"),
        [
            ("he", MyFrozenDict({"h": 1, "e": 1}), "hello", "hello"),
            ("hh", MyFrozenDict({"h": 2}), None, None),
        ],
    )
    def test_has_chord_and_get_chord(self, config_wrapper, trigger, data_key, data_val, expected):
        if data_val is not None:
            config_wrapper.data = {data_key: data_val}
        assert config_wrapper.has_chord(trigger) == (data_val is not None)
        assert config_wrapper.get_chord(trigger) == expected

    @pytest.mark.parametrize(
        ("trigger", "data_key", "data_val", "expected"),
        [
            ("ab", MyFrozenDict({"a": 1, "b": 1}), "AB", "AB"),
            ("zz", None, None, None),
        ],
    )
    def test_has_chip_and_get_chip(self, config_wrapper, trigger, data_key, data_val, expected):
        if data_val is not None:
            config_wrapper.data = {data_key: data_val}
        assert config_wrapper.has_chip(trigger) == (data_val is not None)
        assert config_wrapper.get_chip(trigger) == expected

    def test_get_triggers_returns_list(self, config_wrapper):
        fk = MyFrozenDict({"a": 1})
        config_wrapper.reversed_data = {"out": [fk]}
        assert config_wrapper.get_triggers("out") == [fk]

    def test_get_triggers_returns_none_for_missing(self, config_wrapper):
        assert config_wrapper.get_triggers("missing") is None

    @pytest.mark.parametrize(
        ("blocked", "allowed", "s", "expected"),
        [
            ([], [], "anything", False),
            (["bad"], [], "bad", True),
            (["bad"], [], "good", False),
            ([], ["ok"], "ok", False),
            ([], ["ok"], "not_ok", True),
            (["bad"], ["ok"], "bad", True),
            (["bad"], ["ok"], "ok", False),
            (["bad"], ["ok"], "other", True),
        ],
    )
    def test_filtered(self, config_wrapper, blocked, allowed, s, expected):
        config_wrapper.config.filter.blocked = blocked
        config_wrapper.config.filter.allowed = allowed
        assert config_wrapper.filtered(s) == expected

    def test_make_message_default_format(self, config_wrapper):
        msg = config_wrapper.make_message(["a", "b"], "chord_val")
        assert msg == "['a', 'b'] = chord_val"

    def test_make_message_custom_format(self, config_wrapper):
        config_wrapper.config.notification.message = "trigger: $triggers out: $chord"
        msg = config_wrapper.make_message(["x"], "y")
        assert msg == "trigger: ['x'] out: y"

    def test_make_message_single_trigger(self, config_wrapper):
        msg = config_wrapper.make_message("single", "val")
        assert msg == "single = val"
