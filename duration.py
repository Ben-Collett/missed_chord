from dataclasses import dataclass
from logger import log_warning


@dataclass
class Duration:
    milliseconds: int

    @property
    def seconds(self) -> float:
        return self.milliseconds/1000

    @staticmethod
    def parse(duration, fallback: "Duration") -> "Duration":
        """
        if an int is passed in it is assumed to be in seconds
        if a str is passed in it is assumed milliseconds unless it ends with a s or S and not ms or MS or Ms or mS
        if a value can't be parsed from the string the fallback duration is used
        and a warning is logged

        the duration string can be a decimal it will be rounded to the nearest integer milliseconds
        using bankers rounding

        """

        if duration is None:
            return fallback

        if not isinstance(duration, str) and not isinstance(duration, int) and not isinstance(duration, float):
            log_warning(f"{duration} is not accepted type str,int,float type is {
                        type(duration)}")
            return fallback
        duration = str(duration)

        original_duration = duration
        duration = duration.lower()
        multiplier = 1
        if duration.endswith("ms"):
            duration = duration.removesuffix("ms")
        elif duration.endswith("s"):
            duration = duration.removesuffix("s")
            multiplier = 1000

        try:
            return Duration(round(float(duration) * multiplier))
        except ValueError:
            log_warning(f"couldn't parse duration {
                original_duration}, falling back to {fallback}")
            return fallback
