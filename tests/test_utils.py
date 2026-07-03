import os
from pathlib import Path
import pytest
from my_frozen_dict import MyFrozenDict
from utils import (
    reverse_dict,
    flat_inplace_merge_dicts,
    dicts_to_strings,
    uncapitalize,
    _to_str,
    ascii_only,
    is_on_linux,
    overlap_count,
)


class TestReverseDict:
    @pytest.mark.parametrize(
        ("input_dict", "expected"),
        [
            ({}, {}),
            ({"a": 1}, {1: ["a"]}),
            ({"a": 1, "b": 1}, {1: ["a", "b"]}),
            ({"a": 1, "b": 2}, {1: ["a"], 2: ["b"]}),
            ({"a": 1, "b": 1, "c": 1}, {1: ["a", "b", "c"]}),
        ],
    )
    def test_reverse_dict(self, input_dict, expected):
        assert reverse_dict(input_dict) == expected


class TestFlatInplaceMergeDicts:
    def test_both_none(self):
        flat_inplace_merge_dicts(None, None)

    def test_dict1_none(self):
        flat_inplace_merge_dicts(None, {"a": 1})

    def test_dict2_none(self):
        d = {"a": 1}
        flat_inplace_merge_dicts(d, None)
        assert d == {"a": 1}

    def test_merges_missing_keys(self):
        d1 = {"a": 1}
        d2 = {"b": 2}
        flat_inplace_merge_dicts(d1, d2)
        assert d1 == {"a": 1, "b": 2}

    def test_does_not_overwrite_existing_keys(self):
        d1 = {"a": 1}
        d2 = {"a": 99, "b": 2}
        flat_inplace_merge_dicts(d1, d2)
        assert d1 == {"a": 1, "b": 2}

    def test_empty_dicts(self):
        d1 = {}
        d2 = {}
        flat_inplace_merge_dicts(d1, d2)
        assert d1 == {}


class TestDictsToStrings:
    def test_empty_list(self):
        assert dicts_to_strings([]) == []

    def test_single_dict(self):
        result = dicts_to_strings([MyFrozenDict({"h": 3})])
        assert result == ["hhh"]

    def test_multiple_dicts(self):
        result = dicts_to_strings([
            MyFrozenDict({"h": 2, "e": 1}),
            MyFrozenDict({"w": 1, "o": 2}),
        ])
        assert result == ["hhe", "woo"]

    def test_zero_frequency(self):
        result = dicts_to_strings([MyFrozenDict({"a": 0})])
        assert result == [""]


class TestUncapitalize:
    @pytest.mark.parametrize(
        ("input_str", "expected"),
        [
            ("", ""),
            ("A", "a"),
            ("Hello", "hello"),
            ("HELLO", "hELLO"),
            ("hello", "hello"),
            ("Already", "already"),
        ],
    )
    def test_uncapitalize(self, input_str, expected):
        assert uncapitalize(input_str) == expected


class TestToStr:
    @pytest.mark.parametrize(
        ("input_list", "expected"),
        [
            ([], ""),
            ([0], ""),
            ([0, 0, 0], ""),
            ([65], "A"),
            ([97, 98, 99], "abc"),
            ([0, 65, 0, 66], "AB"),
            ([31], None),
            ([127], None),
            ([128], None),
            ([0, 0, 65, 0, 0], "A"),
        ],
    )
    def test_to_str(self, input_list, expected):
        assert _to_str(input_list) == expected


class TestAsciiOnly:
    def test_empty_chords(self):
        assert ascii_only({"chords": []}) == {}

    def test_valid_chords(self):
        data = {"chords": [[[104, 101], [104, 105]]]}
        result = ascii_only(data)
        assert len(result) == 1
        key = MyFrozenDict({"h": 1, "e": 1})
        assert result[key] == "hi"

    def test_non_ascii_triggers_skipped(self):
        data = {"chords": [[[200], [65]]]}
        assert ascii_only(data) == {}

    def test_non_ascii_outputs_skipped(self):
        data = {"chords": [[[65], [200]]]}
        assert ascii_only(data) == {}

    def test_mixed_valid_and_invalid(self):
        data = {
            "chords": [
                [[104, 105], [104, 105]],
                [[200], [65]],
            ]
        }
        result = ascii_only(data)
        assert len(result) == 1
        key = MyFrozenDict({"h": 1, "i": 1})
        assert result[key] == "hi"

    def test_padding_zeros_ignored(self):
        data = {"chords": [[[0, 104, 0, 101, 0], [104, 105]]]}
        result = ascii_only(data)
        assert len(result) == 1

    def test_output_is_uncapitalized(self):
        data = {"chords": [[[104, 73], [72, 105]]]}
        result = ascii_only(data)
        key = MyFrozenDict({"h": 1, "i": 1})
        assert result[key] == "hi"


class TestIsOnLinux:
    @pytest.mark.parametrize(
        ("platform", "expected"),
        [
            ("linux", True),
            ("darwin", False),
            ("win32", False),
            ("cygwin", False),
        ],
    )
    def test_is_on_linux(self, monkeypatch, platform, expected):
        monkeypatch.setattr("sys.platform", platform)
        assert is_on_linux() == expected


class TestSafeExpandUser:
    def test_non_linux_returns_path_unchanged(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "win32")
        p = Path("/some/path")
        from utils import safe_expand_user
        assert safe_expand_user(p) == p

    def test_linux_no_tilde_returns_path_unchanged(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        p = Path("/some/path")
        from utils import safe_expand_user
        assert safe_expand_user(p) == p

    def test_linux_tilde_without_sudo(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setattr("os.path.expanduser", lambda p: "/home/user" + p[1:])
        monkeypatch.delenv("SUDO_USER", raising=False)
        p = Path("~/config.toml")
        from utils import safe_expand_user
        assert str(safe_expand_user(p)) == "/home/user/config.toml"

    def test_linux_tilde_with_sudo(self, monkeypatch):
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setenv("SUDO_USER", "sudoer")

        class FakePwd:
            @staticmethod
            def getpwnam(user):
                class PW:
                    pw_uid = 1000
                return PW()

            @staticmethod
            def getpwuid(uid):
                class PW:
                    pw_dir = "/home/sudoer"
                return PW()

        import pwd as real_pwd
        monkeypatch.setattr("pwd.getpwnam", FakePwd.getpwnam)
        monkeypatch.setattr("pwd.getpwuid", FakePwd.getpwuid)

        p = Path("~/config.toml")
        from utils import safe_expand_user
        result = safe_expand_user(p)
        assert str(result) == "/home/sudoer/config.toml"


class TestOverlapCount:
    @pytest.mark.parametrize(
        ("s1", "s2", "expected"),
        [
            ("", "", 0),
            ("a", "", 0),
            ("", "a", 0),
            ("abc", "abc", 3),
            ("abc", "abd", 2),
            ("abc", "xyz", 0),
            ("hello", "he", 2),
            ("he", "hello", 2),
            ("abc", "abcde", 3),
            ("abcde", "abc", 3),
            ("abc", "ABC", 0),
        ],
    )
    def test_overlap_count(self, s1, s2, expected):
        assert overlap_count(s1, s2) == expected
