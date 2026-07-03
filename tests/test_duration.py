import pytest
from duration import Duration


class TestDuration:
    @pytest.mark.parametrize(
        ("milliseconds",),
        [
            (0,),
            (1,),
            (1000,),
            (-500,),
        ],
    )
    def test_constructor(self, milliseconds):
        assert Duration(milliseconds).milliseconds == milliseconds

    @pytest.mark.parametrize(
        ("milliseconds", "expected"),
        [
            (0, 0.0),
            (1000, 1.0),
            (1500, 1.5),
            (250, 0.25),
        ],
    )
    def test_seconds_property(self, milliseconds, expected):
        assert Duration(milliseconds).seconds == expected

    @pytest.mark.parametrize(
        ("value", "fallback", "expected"),
        [
            pytest.param(None, Duration(999), Duration(999), id="None returns fallback"),
            pytest.param([], Duration(999), Duration(999), id="invalid type returns fallback"),
            pytest.param({}, Duration(999), Duration(999), id="dict returns fallback"),
            pytest.param(2, Duration(999), Duration(2), id="int treated as ms (no suffix)"),
            pytest.param(0, Duration(999), Duration(0), id="int zero"),
            pytest.param(-1, Duration(999), Duration(-1), id="negative int"),
            pytest.param(1.5, Duration(999), Duration(2), id="float bankers rounded to ms"),
            pytest.param(0.25, Duration(999), Duration(0), id="float fractional rounds to 0"),
            pytest.param("500", Duration(999), Duration(500), id="str no suffix is ms"),
            pytest.param("500ms", Duration(999), Duration(500), id="str ms suffix"),
            pytest.param("2s", Duration(999), Duration(2000), id="str s suffix"),
            pytest.param("1.5s", Duration(999), Duration(1500), id="str decimal seconds"),
            pytest.param("2S", Duration(999), Duration(2000), id="str uppercase S"),
            pytest.param("500MS", Duration(999), Duration(500), id="str uppercase MS"),
            pytest.param("500mS", Duration(999), Duration(500), id="str mixed case mS"),
            pytest.param("500Ms", Duration(999), Duration(500), id="str mixed case Ms"),
            pytest.param("not_a_number", Duration(999), Duration(999), id="unparseable str returns fallback"),
            pytest.param("2.5", Duration(999), Duration(2), id="bankers rounding even"),
            pytest.param("3.5", Duration(999), Duration(4), id="bankers rounding odd"),
        ],
    )
    def test_parse(self, value, fallback, expected):
        result = Duration.parse(value, fallback)
        assert result == expected
        assert isinstance(result, Duration)
