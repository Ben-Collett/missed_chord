import pytest
from chip_loop_utils import ExpectedString, probable_chip
from config_wrapper import ConfigWrapper


class TestExpectedString:
    @pytest.fixture
    def es(self):
        return ExpectedString()

    def test_initially_empty(self, es):
        assert es.is_empty()

    @pytest.mark.parametrize(
        ("value", "expected_empty", "expected_first"),
        [
            ("", True, None),
            ("a", False, "a"),
            ("hello", False, "h"),
            ("abc", False, "a"),
        ],
    )
    def test_set_value(self, es, value, expected_empty, expected_first):
        es.set_value(value)
        assert es.is_empty() == expected_empty
        if not expected_empty:
            assert es.starts_with(expected_first)

    def test_clear(self, es):
        es.set_value("abc")
        es.clear()
        assert es.is_empty()

    @pytest.mark.parametrize(
        ("initial", "ch", "expected"),
        [
            ("", "a", False),
            ("abc", "a", True),
            ("abc", "b", False),
            ("abc", "", False),
        ],
    )
    def test_starts_with(self, es, initial, ch, expected):
        es.set_value(initial)
        assert es.starts_with(ch) == expected

    @pytest.mark.parametrize(
        ("initial", "ch", "expected"),
        [
            ("", None, False),
            ("abc", None, False),
            ("", "a", True),
            ("abc", "a", False),
            ("abc", "b", True),
        ],
    )
    def test_should_clear(self, es, initial, ch, expected):
        es.set_value(initial)
        assert es.should_clear(ch) == expected

    @pytest.mark.parametrize(
        ("initial", "ch", "expected_empty"),
        [
            ("", "a", True),
            ("abc", "a", False),
            ("abc", "b", True),
            ("abc", None, False),
        ],
    )
    def test_clear_if_should(self, es, initial, ch, expected_empty):
        es.set_value(initial)
        es.clear_if_should(ch)
        assert es.is_empty() == expected_empty

    @pytest.mark.parametrize(
        ("initial", "expected_first"),
        [
            ("", ""),
            ("a", "A"),
            ("A", "a"),
            ("abc", "Abc"),
            ("ABC", "aBC"),
            ("hello", "Hello"),
            ("Hello", "hello"),
        ],
    )
    def test_toggle_case(self, es, initial, expected_first):
        es.set_value(initial)
        es.toggle_case()
        if initial == "":
            assert es.is_empty()
        else:
            assert es._value[0] == expected_first[0]

    @pytest.mark.parametrize(
        ("initial", "expected", "expected_empty"),
        [
            ("", "", True),
            ("a", "", True),
            ("abc", "bc", False),
            ("hello", "ello", False),
        ],
    )
    def test_safe_remove_first(self, es, initial, expected, expected_empty):
        es.set_value(initial)
        es.safe_remove_first()
        result = "".join(es._value)
        assert result == expected
        assert es.is_empty() == expected_empty

    @pytest.mark.parametrize(
        ("initial", "ch", "expected"),
        [
            ("", "a", "a"),
            ("a", "b", "ab"),
            ("hello", "!", "hello!"),
        ],
    )
    def test_append(self, es, initial, ch, expected):
        es.set_value(initial)
        es.append(ch)
        assert "".join(es._value) == expected

    def test_chain_operations(self, es):
        es.set_value("hello")
        es.safe_remove_first()
        assert "".join(es._value) == "ello"
        es.append("!")
        assert "".join(es._value) == "ello!"
        es.toggle_case()
        assert es._value[0] == "E"
        es.clear()
        assert es.is_empty()


class TestProbableChip:
    @pytest.mark.parametrize(
        ("prev_word", "chip_map", "expected"),
        [
            pytest.param("hello", {"hello": "h"}, "h", id="exact match"),
            pytest.param("WORLD", {"world": "w"}, "W",
                         id="upper>1 falls back to lower, returns upper"),
            pytest.param("World", {"world": "w"}, "W",
                         id="upper==1 falls back to lower, capitalizeith"),
            pytest.param("world", {"world": "w"}, "w",
                         id="all lower, exact match returns as-is"),
            pytest.param("HELLO", {"hello": "hi"}, "HI",
                         id="upper>1 returns full upper"),
            pytest.param("Test", {"test": "value"},
                         "Value", id="capitalize first letter"),
            pytest.param("unknown", {"hello": "h"},
                         None, id="no match returns None"),
            pytest.param("baz", {"bar": "x"}, None,
                         id="no match for lower variant either"),
            pytest.param("abc", {"xyz": "z"}, None,
                         id="different word no match"),
            pytest.param("", {"": "empty"}, "empty",
                         id="empty string exact match"),
            pytest.param("MIX", {"mix": "result"}, "RESULT",
                         id="mixed case >1 upper returns full upper"),
        ],
    )
    def test_probable_chip(self, monkeypatch, prev_word, chip_map, expected):
        class FakeConfigWrapper(ConfigWrapper):
            def get_chip(self, trigger):
                return chip_map.get(trigger)

        fw = FakeConfigWrapper()
        assert probable_chip(prev_word, fw) == expected
