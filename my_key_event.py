from typing import Self


class MyKeyEvent:
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
