class Duration:
    __slots__ = ("_seconds",)

    def __init__(self, *, seconds: float | None = None, milliseconds: float | None = None):
        if seconds is None and milliseconds is None:
            raise ValueError("Provide either seconds or milliseconds")

        if seconds is not None and milliseconds is not None:
            raise ValueError("Provide only one of seconds or milliseconds")

        if seconds is not None:
            self._seconds = float(seconds)
        else:
            self._seconds = float(milliseconds) / 1000.0

    @property
    def seconds(self) -> float:
        return self._seconds

    @property
    def milliseconds(self) -> float:
        return self._seconds * 1000.0

    def __float__(self) -> float:
        """Allows: time.sleep(Duration(...))"""
        return self._seconds

    def __repr__(self) -> str:
        return f"Duration(seconds={self._seconds})"


def safe_get_duration(duration_ms, duration_s, default):
    if duration_ms:
        return Duration(milliseconds=duration_ms)
    elif duration_s:
        return Duration(seconds=duration_s)
    else:
        return default
