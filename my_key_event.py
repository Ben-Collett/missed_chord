from typing import Self
from typing import Optional


class MyKeyEvent:
    def to_utf(self, shift_down: bool) -> Optional[str]:
        name = self.name

        if len(name) == 1 and shift_down:
            return name.upper()
        if len(name) == 1:
            return name

        if name == "space":
            return " "
        if name == "tab":
            return "\t"
        if name == "return":
            return "\n"
        return None

    @property
    def is_arrow(self):
        arrows = ["left", "down", "up", "right"]
        return self.name in arrows

    @property
    def is_backspace(self):
        return self.name == "backspace"

    @property
    def is_down_event(self):
        return self.value == 1

    @property
    def is_up_event(self):
        return not self.is_down_event

    def __init__(self, name: str, value: int, modifiers: list[str]):
        self.name: str = name
        self.value: int = value
        self.modifiers = modifiers

    @staticmethod
    def parse_line(line: str) -> Self | None:
        parts = line.strip().split()  # splits on any whitespace

        if len(parts) < 2:
            return None

        name, value, *modifiers = parts

        try:
            value = int(value)
        except Exception:
            return None

        return MyKeyEvent(name, value, modifiers)


class TerminateEvent():
    pass


TERMINATE_EVENT = TerminateEvent()
