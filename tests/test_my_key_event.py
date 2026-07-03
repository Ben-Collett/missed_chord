import pytest
from unittest.mock import MagicMock, patch
from my_key_event import MyKeyEvent, TerminateEvent, TERMINATE_EVENT
from modifier_utils import DownMods


class TestMyKeyEvent:
    def test_from_keyboard_event_down(self):
        mock_event = MagicMock()
        mock_event.event_type = "down"
        mock_event.name = "a"
        mock_event.modifiers = []

        result = MyKeyEvent.from_keyboard_event(mock_event)
        assert result.name == "a"
        assert result.is_down
        assert not result.modifiers.shift_down

    def test_from_keyboard_event_up(self):
        mock_event = MagicMock()
        mock_event.event_type = "up"
        mock_event.name = "a"
        mock_event.modifiers = ["shift"]

        result = MyKeyEvent.from_keyboard_event(mock_event)
        assert result.name == "a"
        assert not result.is_down
        assert result.modifiers.shift_down

    def test_from_keyboard_event_none_name(self):
        mock_event = MagicMock()
        mock_event.event_type = "down"
        mock_event.name = None
        mock_event.modifiers = []

        result = MyKeyEvent.from_keyboard_event(mock_event)
        assert result.name == ""

    @pytest.mark.parametrize(
        ("name", "mods", "expected"),
        [
            ("a", DownMods(), "a"),
            ("A", DownMods(), "A"),
            ("space", DownMods(), " "),
            ("tab", DownMods(), "\t"),
            ("return", DownMods(), "\n"),
            ("enter", DownMods(), None),
            ("escape", DownMods(), None),
            ("ctrl", DownMods(), None),
            ("f1", DownMods(), None),
            ("a", DownMods(alt_down=True), None),
            ("a", DownMods(ctrl_down=True), None),
            ("a", DownMods(meta_down=True), None),
            ("a", DownMods(shift_down=True), "a"),
            ("A", DownMods(shift_down=True), "A"),
        ],
    )
    def test_to_utf(self, name, mods, expected):
        event = MyKeyEvent(name=name, is_down=True, modifiers=mods)
        assert event.to_utf() == expected

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("left", True),
            ("down", True),
            ("up", True),
            ("right", True),
            ("a", False),
            ("space", False),
            ("backspace", False),
        ],
    )
    def test_is_arrow(self, name, expected):
        event = MyKeyEvent(name=name, is_down=True, modifiers=DownMods())
        assert event.is_arrow == expected

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("backspace", True),
            ("a", False),
            ("space", False),
            ("delete", False),
        ],
    )
    def test_is_backspace(self, name, expected):
        event = MyKeyEvent(name=name, is_down=True, modifiers=DownMods())
        assert event.is_backspace == expected

    def test_is_up_true_when_not_down(self):
        event = MyKeyEvent(name="a", is_down=False, modifiers=DownMods())
        assert event.is_up

    def test_is_up_false_when_down(self):
        event = MyKeyEvent(name="a", is_down=True, modifiers=DownMods())
        assert not event.is_up


class TestTerminateEvent:
    def test_terminate_event_class(self):
        assert isinstance(TERMINATE_EVENT, TerminateEvent)

    def test_terminate_event_is_distinct(self):
        assert TERMINATE_EVENT is TERMINATE_EVENT

    def test_multiple_terminate_events(self):
        t1 = TerminateEvent()
        t2 = TerminateEvent()
        assert isinstance(t1, TerminateEvent)
        assert isinstance(t2, TerminateEvent)
