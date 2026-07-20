import pytest
from modifier_utils import DownMods


class TestDownMods:
    def test_defaults_are_false(self):
        m = DownMods()
        assert not m.shift_down
        assert not m.ctrl_down
        assert not m.alt_down
        assert not m.meta_down

    @pytest.mark.parametrize(
        ("mod", "attr", "expected"),
        [
            ("shift", "shift_down", True),
            ("SHIFT", "shift_down", True),
            ("Shift", "shift_down", True),
            ("ctrl", "ctrl_down", True),
            ("CTRL", "ctrl_down", True),
            ("alt", "alt_down", True),
            ("ALT", "alt_down", True),
            ("windows", "meta_down", True),
            ("Windows", "meta_down", True),
            ("WINDOWS", "meta_down", True),
            ("unknown", "shift_down", False),
            ("caps", "ctrl_down", False),
        ],
    )
    def test_update_from_mod(self, mod, attr, expected):
        m = DownMods()
        m.update_from_mod(mod)
        assert getattr(m, attr) == expected

    def test_update_from_mod_only_sets_one(self):
        m = DownMods()
        m.update_from_mod("shift")
        assert m.shift_down
        assert not m.ctrl_down
        assert not m.alt_down
        assert not m.meta_down

    def test_update_from_mod_multiple_calls(self):
        m = DownMods()
        m.update_from_mod("shift")
        m.update_from_mod("ctrl")
        m.update_from_mod("alt")
        assert m.shift_down
        assert m.ctrl_down
        assert m.alt_down
        assert not m.meta_down

    @pytest.mark.parametrize(
        ("event_name", "is_down", "modifiers", "expected"),
        [
            ("a", True, [], DownMods(shift_down=False,
             ctrl_down=False, alt_down=False, meta_down=False)),
            ("shift", True, [], DownMods(shift_down=True)),
            ("shift", False, [], DownMods(shift_down=False)),
            ("a", True, ["shift"], DownMods(shift_down=True)),
            ("a", True, ["ctrl", "alt"], DownMods(
                ctrl_down=True, alt_down=True)),
            ("ctrl", True, ["shift"], DownMods(
                shift_down=True, ctrl_down=True)),
            ("a", False, ["shift"], DownMods(shift_down=True)),
            ("a", False, [], DownMods()),
            ("windows", True, ["ctrl"], DownMods(
                ctrl_down=True, meta_down=True)),
            ("windows", True, [], DownMods(meta_down=True)),
        ],
    )
    def test_from_event_data(self, event_name, is_down, modifiers, expected):
        result = DownMods.from_event_data(event_name, is_down, modifiers)
        assert result == expected
