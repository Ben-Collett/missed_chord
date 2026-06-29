from dataclasses import dataclass
from typing import Optional
import keyboard
from keyboard._keyboard_event import KeyboardEvent

from modifier_utils import DownMods


@dataclass
class MyKeyEvent:
    name: str
    is_down: bool
    modifiers: DownMods

    @staticmethod
    def from_keyboard_event(event: KeyboardEvent) -> "MyKeyEvent":
        is_down = event.event_type == keyboard.KEY_DOWN
        name = event.name or ""
        down_mods = DownMods.from_event_data(
            name, is_down, event.modifiers or [])
        return MyKeyEvent(name, is_down, down_mods)

    def to_utf(self) -> Optional[str]:
        name = self.name
        mods = self.modifiers
        if mods.alt_down or mods.ctrl_down or mods.meta_down:
            return None

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
    def is_up(self):
        return not self.is_down


class TerminateEvent():
    pass


TERMINATE_EVENT = TerminateEvent()
