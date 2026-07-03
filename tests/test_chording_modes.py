import pytest
from chording_modes import ChordingMode


class TestChordingMode:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("charachorder", ChordingMode.CHARA_CHORDER),
            ("fuzzy chips", ChordingMode.FUZZY_CHIPS),
        ],
    )
    def test_parse_valid(self, value, expected):
        assert ChordingMode.parse(value) == expected

    @pytest.mark.parametrize(
        "value",
        ["", "invalid", "chara", "fuzzy", "charachorder "],
    )
    def test_parse_invalid_defaults_to_chara(self, value):
        assert ChordingMode.parse(value) == ChordingMode.CHARA_CHORDER
