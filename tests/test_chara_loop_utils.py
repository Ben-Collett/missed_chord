import pytest
from chara_loop_utils import captlized_and_uncaptlized, append_captlized_and_uncaptlized


class TestCaptlizedAndUncaptlized:
    @pytest.mark.parametrize(
        ("word", "expected"),
        [
            ("a", ("A", "a")),
            ("hello", ("Hello", "hello")),
            ("Hello", ("Hello", "hello")),
            ("HELLO", ("HELLO", "hELLO")),
            ("hELLO", ("HELLO", "hELLO")),
            ("mississippi", ("Mississippi", "mississippi")),
            ("X", ("X", "x")),
        ],
    )
    def test_returns_cap_and_uncap(self, word, expected):
        assert captlized_and_uncaptlized(word) == expected

    def test_empty_raises_assertion(self):
        with pytest.raises(AssertionError, match="why are you trying captlized an empty word dummy"):
            captlized_and_uncaptlized("")

    def test_round_trip_preserves_rest(self):
        cap, uncap = captlized_and_uncaptlized("hElLo")
        assert cap[1:] == "ElLo"
        assert uncap[1:] == "ElLo"


class TestAppendCaptlizedAndUncaptlized:
    @pytest.mark.parametrize(
        ("initial", "word", "expected"),
        [
            ([], "hello", ["Hello", "hello"]),
            ([], "a", ["A", "a"]),
            ([], "Test", ["Test", "test"]),
            (["foo"], "bar", ["foo", "Bar", "bar"]),
            (["pre", "existing"], "x", ["pre", "existing", "X", "x"]),
        ],
    )
    def test_appends_both_forms(self, initial, word, expected):
        append_captlized_and_uncaptlized(initial, word)
        assert initial == expected

    def test_does_not_mutate_other_lists(self):
        ls1 = ["a"]
        ls2 = ["b"]
        append_captlized_and_uncaptlized(ls1, "x")
        assert ls1 == ["a", "X", "x"]
        assert ls2 == ["b"]

    def test_empty_word_raises_assertion(self):
        with pytest.raises(AssertionError):
            append_captlized_and_uncaptlized([], "")
