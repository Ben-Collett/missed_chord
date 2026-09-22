
from enum import Enum


class LoggingMode(Enum):
    LOAD = "load"
    OVERWRITE = "overwrite"
    INCREMENT = "increment"

    @staticmethod
    def parse(value: str) -> "LoggingMode":
        modes = [member.value for member in LoggingMode]
        if value in modes:
            return LoggingMode(value)
        print(f"{value} is not a valid logging mode: {modes}")
        print(f"defaulting to {LoggingMode.LOAD.value}")
        return LoggingMode.LOAD
